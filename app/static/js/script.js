// Basic JavaScript file for any dynamic interactions
// For example, handling Bootstrap components or custom client-side logic

$(document).ready(function(){
    // Example: Initialize Bootstrap tooltips (if you use them)
    // $('[data-toggle="tooltip"]').tooltip();

    // Example: Dismiss alerts automatically after some time
    window.setTimeout(function() {
        $(".alert").fadeTo(500, 0).slideUp(500, function(){
            $(this).remove();
        });
    }, 5000); // 5 seconds
});

// Add any other global JavaScript functions or initializations here.
// For specific page logic, it's often better to include a separate JS file
// or use inline script tags in the respective templates.

console.log("Main script.js loaded.");
