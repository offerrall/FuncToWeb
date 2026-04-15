(function() {
    'use strict';
    
    window.toggleGroup = function(button) {
        const content = button.nextElementSibling;
        button.classList.toggle('active');
        content.classList.toggle('active');
    };
    
    function initializeGroups() {
        const groups = document.querySelectorAll('.functoweb-group-header');
        groups.forEach(function(header) {
            header.addEventListener('click', function() {
                toggleGroup(this);
            });
        });
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeGroups);
    } else {
        initializeGroups();
    }
})();