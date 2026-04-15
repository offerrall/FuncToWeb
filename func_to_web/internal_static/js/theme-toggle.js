(function() {
    const stored = localStorage.getItem('functoweb-theme');
    const theme = stored || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme;
    if (theme === 'dark') {
        document.documentElement.classList.add('dark-mode');
    }
})();

(function() {
    'use strict';
    
    function getPreferredTheme() {
        const stored = localStorage.getItem('functoweb-theme');
        if (stored) return stored;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        document.documentElement.style.colorScheme = theme;
        
        if (theme === 'dark') {
            document.documentElement.classList.add('dark-mode');
        } else {
            document.documentElement.classList.remove('dark-mode');
        }
        
        localStorage.setItem('functoweb-theme', theme);
        updateThemeIcon(theme);
    }
    
    function updateThemeIcon(theme) {
        const sunIcon = document.querySelector('.sun-icon');
        const moonIcon = document.querySelector('.moon-icon');
        
        if (!sunIcon || !moonIcon) return;
        
        if (theme === 'dark') {
            sunIcon.classList.remove('active');
            moonIcon.classList.add('active');
        } else {
            moonIcon.classList.remove('active');
            sunIcon.classList.add('active');
        }
    }
    
    window.toggleTheme = function() {
        const current = document.documentElement.getAttribute('data-theme') || getPreferredTheme();
        const next = current === 'dark' ? 'light' : 'dark';
        setTheme(next);
    };
    
    function initThemeIcon() {
        const theme = document.documentElement.getAttribute('data-theme') || getPreferredTheme();
        updateThemeIcon(theme);
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initThemeIcon);
    } else {
        initThemeIcon();
    }
})();