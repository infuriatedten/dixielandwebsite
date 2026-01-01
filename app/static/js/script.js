// Enhanced JavaScript for modern interactions and animations
$(document).ready(function(){
    // Initialize Bootstrap tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    if (typeof bootstrap !== 'undefined') {
        var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
        var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
            return new bootstrap.Dropdown(dropdownToggleEl);
        });
    }

    // Enhanced alert dismissal with better animations
    window.setTimeout(function() {
        $(".alert").each(function(index) {
            $(this).delay(index * 200).fadeOut(800, function(){
                $(this).slideUp(300, function(){
                    $(this).remove();
                });
            });
        });
    }, 4000);

    // Add loading states to buttons
    $('form').on('submit', function() {
        const submitBtn = $(this).find('button[type="submit"]');
        const originalText = submitBtn.text();
        submitBtn.prop('disabled', true)
               .html('<span class="spinner-border spinner-border-sm me-2" role="status"></span>Loading...');

        // Reset after 10 seconds as fallback
        setTimeout(function() {
            submitBtn.prop('disabled', false).text(originalText);
        }, 10000);
    });

    // Enhanced table interactions
    $('.table tbody tr').hover(
        function() {
            $(this).addClass('table-hover-effect');
        },
        function() {
            $(this).removeClass('table-hover-effect');
        }
    );

    // Smooth scrolling for anchor links
    $('a[href^="#"]:not([data-bs-toggle="dropdown"])').on('click', function(event) {
        const target = $(this.getAttribute('href'));
        if (target.length) {
            event.preventDefault();
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 100
            }, 1000);
        }
    });

    // Add ripple effect to buttons
    $('.btn').on('click', function(e) {
        const btn = $(this);
        const ripple = $('<span class="ripple"></span>');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;

        ripple.css({
            width: size,
            height: size,
            left: x,
            top: y
        });

        btn.append(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    });

    // Form validation enhancements
    $('.needs-validation').on('submit', function(event) {
        if (!this.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();

            // Focus on first invalid field
            const firstInvalid = $(this).find(':invalid').first();
            if (firstInvalid.length) {
                firstInvalid.focus();
                $('html, body').animate({
                    scrollTop: firstInvalid.offset().top - 100
                }, 500);
            }
        }
        $(this).addClass('was-validated');
    });

    // Enhanced card hover effects
    $('.card').hover(
        function() {
            $(this).addClass('card-hover');
        },
        function() {
            $(this).removeClass('card-hover');
        }
    );

    // Auto-hide flash messages on scroll
    let lastScrollTop = 0;
    $(window).scroll(function() {
        const st = $(this).scrollTop();
        if (st > lastScrollTop && st > 100) {
            $('.alert').fadeOut(300);
        }
        lastScrollTop = st;
    });

    // Add loading spinner for AJAX calls
    $(document).ajaxStart(function() {
        $('body').addClass('loading');
    }).ajaxStop(function() {
        $('body').removeClass('loading');
    });

    // Initialize number formatting
    $('.currency').each(function() {
        const value = parseFloat($(this).text().replace(/[^0-9.-]+/g, ''));
        if (!isNaN(value)) {
            $(this).text('$' + value.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }));
        }
    });

    // Add confirmation dialogs for dangerous actions
    $('.btn-danger, .delete-btn').on('click', function(e) {
        if (!$(this).hasClass('confirmed')) {
            e.preventDefault();
            const action = $(this).data('action') || 'perform this action';
            if (confirm(`Are you sure you want to ${action}? This action cannot be undone.`)) {
                $(this).addClass('confirmed').click();
            }
        }
    });

    console.log("Enhanced script.js loaded with modern interactions.");
});

// Add CSS for ripple effect and other enhancements
const style = document.createElement('style');
style.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255,255,255,0.6);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }

    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }

    .btn {
        position: relative;
        overflow: hidden;
    }

    .table-hover-effect {
        background-color: rgba(102, 126, 234, 0.1) !important;
    }

    .card-hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 12px 40px rgba(0,0,0,0.15) !important;
    }

    .loading {
        cursor: wait;
    }

    .loading * {
        pointer-events: none;
    }

    .spinner-border-sm {
        width: 1rem;
        height: 1rem;
    }
`;
document.head.appendChild(style);