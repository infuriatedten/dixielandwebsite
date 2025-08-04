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
    -- This is a placeholder function. In a real scenario, you would use the game's API
    -- to get live data. For example:
    -- local balance = g_currentMission.missionStats.money
    -- local fields_owned = #g_fieldManager:getFieldsForFarm(g_currentMission.farmId)

    return {
        balance = math.random(5000, 150000),
        fields_owned = math.random(1, 10),
        total_yield = math.random(10000, 50000),
        equipment_owned = math.random(2, 25)
    }
end

function WebPortalIntegration:syncWithPortal()
    Logging.info("WebPortalIntegration: Starting sync with portal.")
    local playerData = self:getPlayerData()

    -- 1. Update Balance
    local balanceUrl = self.portalUrl .. "/api/fs25/update_balance"
    local balanceData = {
        farmer_id = self.farmerId,
        balance = playerData.balance
    }
    g_httpClient:post(balanceUrl, g_json.encode(balanceData), { "Content-Type: application/json" }, "onBalanceUpdateResponse", self)

    -- 2. Update Stats
    local statsUrl = self.portalUrl .. "/api/fs25/update_stats"
    local statsData = {
        farmer_id = self.farmerId,
        fields_owned = playerData.fields_owned,
        total_yield = playerData.total_yield,
        equipment_owned = playerData.equipment_owned
    }
    g_httpClient:post(statsUrl, g_json.encode(statsData), { "Content-Type: application/json" }, "onStatsUpdateResponse", self)

    -- 3. Get Notifications
    local notificationsUrl = self.portalUrl .. "/api/fs25/get_notifications?farmer_id=" .. self.farmerId
    g_httpClient:get(notificationsUrl, "onNotificationsResponse", self)
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

function WebPortalIntegration:onNotificationsResponse(success, result, headers)
    if success then
        local data, err = g_json.decode(result)
        if data then
            self.notifications = data
            Logging.info("WebPortalIntegration: Notifications received successfully.")
            self.lastSyncSuccessful = true
        else
            Logging.error("WebPortalIntegration: Failed to parse notifications JSON. Error: " .. tostring(err))
            self.lastSyncSuccessful = false
            self.errorDisplayTime = 5000
        end
    else
        Logging.error("WebPortalIntegration: Failed to get notifications. Code: " .. tostring(result))
        self.lastSyncSuccessful = false
        self.errorDisplayTime = 5000
    end
end
