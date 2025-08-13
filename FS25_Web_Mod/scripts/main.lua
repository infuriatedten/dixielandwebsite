---
-- WebPortalIntegration
--
-- @author: Jules
-- @version: 1.0.0.0
--
-- This script handles the integration with the web portal, sending player data
-- and receiving notifications.
---

WebPortalIntegration = {}
local WebPortalIntegration_mt = Class(WebPortalIntegration, Script)

-- Register the mod
addModEventListener(WebPortalIntegration)

-- Update interval in milliseconds
local UPDATE_INTERVAL = 30000 -- 30 seconds

function WebPortalIntegration:new(customMt)
    local self = WebPortalIntegration:superClass():new(customMt or WebPortalIntegration_mt)

    self.updateTimer = UPDATE_INTERVAL
    self.notifications = nil
    self.portalUrl = nil
    self.farmerId = nil
    self.lastSyncSuccessful = true
    self.errorDisplayTime = 0

    return self
end

function WebPortalIntegration:load(xmlFile)
    local baseDir = getDirectory(xmlFile)
    local configFile = baseDir .. "config.xml"

    local xml, err = g_xml.load(configFile)
    if err ~= nil then
        Logging.error("WebPortalIntegration: Could not load config.xml: " .. err)
        self.configError = "Error: Could not load config.xml."
        return
    end

    self.portalUrl = xml:getValue("configuration.settings#portalUrl")
    self.farmerId = xml:getValue("configuration.settings#farmerId")

    if self.portalUrl == nil or self.farmerId == nil or self.portalUrl == "" or self.farmerId == "" then
        Logging.error("WebPortalIntegration: 'portalUrl' or 'farmerId' is not set in config.xml.")
        self.configError = "Error: 'portalUrl' or 'farmerId' not set in config.xml."
    else
        Logging.info("WebPortalIntegration: Mod loaded and configured for Farmer ID " .. self.farmerId)
    end
end

function WebPortalIntegration:update(dt)
    if self.configError then
        return
    end

    self.updateTimer = self.updateTimer - dt
    if self.updateTimer <= 0 then
        self:syncWithPortal()
        self.updateTimer = UPDATE_INTERVAL
    end

    if self.errorDisplayTime > 0 then
        self.errorDisplayTime = self.errorDisplayTime - dt
    end
end

function WebPortalIntegration:draw()
    if self.configError then
        renderText(0.5, 0.5, 0.02, self.configError, true)
        return
    end

    local textToDraw = ""
    if self.notifications then
        textToDraw = string.format("Portal: %d messages, %d notifications.",
                                   self.notifications.unread_messages or 0,
                                   self.notifications.unread_notifications or 0)
    else
        textToDraw = "Portal: Awaiting data..."
    end

    if self.errorDisplayTime > 0 and not self.lastSyncSuccessful then
        renderText(0.98, 0.95, 0.015, "Portal: Sync Error", false, {1, 0.2, 0.2}) -- Red text
    else
        renderText(0.98, 0.95, 0.015, textToDraw, false)
    end
end

function WebPortalIntegration:getPlayerData()
    local playerData = {}
    
    -- Get real game data
    if g_currentMission and g_currentMission.missionStats then
        playerData.balance = g_currentMission.missionStats.money or 0
    else
        playerData.balance = 0
    end
    
    -- Count owned fields
    playerData.fields_owned = 0
    if g_fieldManager and g_currentMission then
        local farmId = g_currentMission.player.farmId or 1
        local fields = g_fieldManager:getFieldsOwnedByFarm(farmId)
        if fields then
            playerData.fields_owned = #fields
        end
    end
    
    -- Count equipment
    playerData.equipment_owned = 0
    if g_currentMission and g_currentMission.vehicleSystem then
        local vehicles = g_currentMission.vehicleSystem.vehicles
        if vehicles then
            for _, vehicle in pairs(vehicles) do
                if vehicle.ownerFarmId == (g_currentMission.player.farmId or 1) then
                    playerData.equipment_owned = playerData.equipment_owned + 1
                end
            end
        end
    end
    
    -- Calculate total yield (approximate from silos)
    playerData.total_yield = 0
    local siloData = self:getSiloData()
    for _, silo in ipairs(siloData) do
        playerData.total_yield = playerData.total_yield + silo.quantity
    end
    
    return playerData
end

function WebPortalIntegration:getSiloData()
    local siloContents = {}
    
    if not g_currentMission or not g_currentMission.storageSystem then
        return siloContents
    end
    
    local farmId = g_currentMission.player.farmId or 1
    local storages = g_currentMission.storageSystem:getStorages()
    
    for _, storage in pairs(storages) do
        if storage.ownerFarmId == farmId and storage.capacity and storage.capacity > 0 then
            for fillTypeIndex, amount in pairs(storage.fillLevels) do
                if amount > 0 then
                    local fillType = g_fillTypeManager:getFillTypeByIndex(fillTypeIndex)
                    if fillType then
                        table.insert(siloContents, {
                            crop_type = fillType.name or fillType.title or "Unknown",
                            quantity = amount,
                            capacity = storage.capacity
                        })
                    end
                end
            end
        end
    end
    
    return siloContents
end

function WebPortalIntegration:syncWithPortal()
    Logging.info("WebPortalIntegration: Starting sync with portal.")
    local playerData = self:getPlayerData()
    local siloData = self:getSiloData()

    -- 1. Update Balance
    local balanceUrl = self.portalUrl .. "/api/fs25/update_balance"
    local balanceData = {
        farmer_id = tonumber(self.farmerId),
        balance = playerData.balance
    }
    self:makeHttpRequest("POST", balanceUrl, balanceData, "onBalanceUpdateResponse")

    -- 2. Update Stats
    local statsUrl = self.portalUrl .. "/api/fs25/update_stats"
    local statsData = {
        farmer_id = tonumber(self.farmerId),
        fields_owned = playerData.fields_owned,
        total_yield = playerData.total_yield,
        equipment_owned = playerData.equipment_owned
    }
    self:makeHttpRequest("POST", statsUrl, statsData, "onStatsUpdateResponse")

    -- 3. Update Silo Contents
    if #siloData > 0 then
        local siloUrl = self.portalUrl .. "/api/fs25/update_silo"
        local siloRequestData = {
            farmer_id = tonumber(self.farmerId),
            silo_contents = siloData
        }
        self:makeHttpRequest("POST", siloUrl, siloRequestData, "onSiloUpdateResponse")
    end

    -- 4. Get Notifications
    local notificationsUrl = self.portalUrl .. "/api/fs25/get_notifications?farmer_id=" .. self.farmerId
    self:makeHttpRequest("GET", notificationsUrl, nil, "onNotificationsResponse")
end

function WebPortalIntegration:makeHttpRequest(method, url, data, callback)
    -- FS25 HTTP implementation
    if method == "POST" and data then
        local jsonData = self:encodeJson(data)
        local headers = "Content-Type: application/json\r\n"
        HTTPUtil.post(url, jsonData, headers, callback, self)
    elseif method == "GET" then
        HTTPUtil.get(url, callback, self)
    end
end

function WebPortalIntegration:encodeJson(data)
    -- Simple JSON encoder for FS25
    local function encode_value(val)
        local type_val = type(val)
        if type_val == "string" then
            return '"' .. val:gsub('"', '\\"') .. '"'
        elseif type_val == "number" then
            return tostring(val)
        elseif type_val == "boolean" then
            return val and "true" or "false"
        elseif type_val == "table" then
            local is_array = true
            local count = 0
            for k, v in pairs(val) do
                count = count + 1
                if type(k) ~= "number" or k ~= count then
                    is_array = false
                    break
                end
            end
            
            if is_array then
                local arr = {}
                for i, v in ipairs(val) do
                    table.insert(arr, encode_value(v))
                end
                return "[" .. table.concat(arr, ",") .. "]"
            else
                local obj = {}
                for k, v in pairs(val) do
                    table.insert(obj, '"' .. tostring(k) .. '":' .. encode_value(v))
                end
                return "{" .. table.concat(obj, ",") .. "}"
            end
        else
            return "null"
        end
    end
    return encode_value(data)
end

-- Callbacks for HTTP requests
function WebPortalIntegration:onBalanceUpdateResponse(success, result, headers)
    if success then
        Logging.info("WebPortalIntegration: Balance updated successfully.")
        self.lastSyncSuccessful = true
    else
        Logging.error("WebPortalIntegration: Failed to update balance. Code: " .. tostring(result))
        self.lastSyncSuccessful = false
        self.errorDisplayTime = 5000 -- Show error for 5 seconds
    end
end

function WebPortalIntegration:onStatsUpdateResponse(success, result, headers)
    if success then
        Logging.info("WebPortalIntegration: Stats updated successfully.")
        self.lastSyncSuccessful = true
    else
        Logging.error("WebPortalIntegration: Failed to update stats. Code: " .. tostring(result))
        self.lastSyncSuccessful = false
        self.errorDisplayTime = 5000 -- Show error for 5 seconds
    end
end

function WebPortalIntegration:onSiloUpdateResponse(success, result, headers)
    if success then
        Logging.info("WebPortalIntegration: Silo contents updated successfully.")
        self.lastSyncSuccessful = true
    else
        Logging.error("WebPortalIntegration: Failed to update silo contents. Code: " .. tostring(result))
        self.lastSyncSuccessful = false
        self.errorDisplayTime = 5000
    end
end

function WebPortalIntegration:onNotificationsResponse(success, result, headers)
    if success then
        -- Simple JSON parser for FS25
        local data = self:parseSimpleJson(result)
        if data then
            self.notifications = data
            Logging.info("WebPortalIntegration: Notifications received successfully.")
            self.lastSyncSuccessful = true
        else
            Logging.error("WebPortalIntegration: Failed to parse notifications JSON.")
            self.lastSyncSuccessful = false
            self.errorDisplayTime = 5000
        end
    else
        Logging.error("WebPortalIntegration: Failed to get notifications. Code: " .. tostring(result))
        self.lastSyncSuccessful = false
        self.errorDisplayTime = 5000
    end
end

function WebPortalIntegration:parseSimpleJson(jsonString)
    -- Simple JSON parser for basic responses
    if not jsonString or jsonString == "" then
        return nil
    end
    
    -- Remove whitespace
    jsonString = jsonString:gsub("%s+", "")
    
    -- Extract basic values
    local data = {}
    
    -- Extract farmer_id
    local farmer_id = jsonString:match('"farmer_id":"?([^",}]+)"?')
    if farmer_id then
        data.farmer_id = farmer_id
    end
    
    -- Extract unread_notifications
    local notifications = jsonString:match('"unread_notifications":(%d+)')
    if notifications then
        data.unread_notifications = tonumber(notifications)
    end
    
    -- Extract unread_messages
    local messages = jsonString:match('"unread_messages":(%d+)')
    if messages then
        data.unread_messages = tonumber(messages)
    end
    
    return data
end

-- Mod lifecycle functions
function WebPortalIntegration:loadMap(name)
    Logging.info("WebPortalIntegration: Map loaded, starting integration.")
end

function WebPortalIntegration:deleteMap()
    Logging.info("WebPortalIntegration: Map unloaded, stopping integration.")
end

function WebPortalIntegration:keyEvent(unicode, sym, modifier, isDown)
    -- Handle any key events if needed
end

function WebPortalIntegration:mouseEvent(posX, posY, isDown, isUp, button)
    -- Handle mouse events if needed
end

-- Initialize the mod
local webPortalIntegration = WebPortalIntegration:new()

-- Load configuration
local modDirectory = g_currentModDirectory
if modDirectory then
    webPortalIntegration:load(modDirectory .. "modDesc.xml")
end
