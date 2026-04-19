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
    if (new URLSearchParams(location.search).get('__embed') !== '1') return;

    function applyEmbed() {
        document.querySelector('.theme-toggle')?.remove();
        document.querySelector('.functoweb-sidebar')?.remove();
        document.querySelector('.functoweb-sidebar-mobile-toggle')?.remove();
        document.querySelector('.functoweb-sidebar-overlay')?.remove();

        document.documentElement.style.setProperty('background', 'transparent', 'important');
        document.body.style.setProperty('background', 'transparent', 'important');

        const container = document.querySelector('.functoweb-container');
        if (container) {
            container.style.setProperty('max-width', 'none', 'important');
            container.style.setProperty('background', 'transparent', 'important');
            container.style.setProperty('box-shadow', 'none', 'important');
            container.style.setProperty('border', 'none', 'important');
            container.style.setProperty('padding', '0', 'important');
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyEmbed);
    } else {
        applyEmbed();
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