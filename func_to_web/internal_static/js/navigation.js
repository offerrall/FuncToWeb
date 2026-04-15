window.toggleSidebarMobile = function() {
    const sidebar = document.querySelector('.functoweb-sidebar');
    const overlay = document.querySelector('.functoweb-sidebar-overlay');
    
    if (!sidebar) return;

    if (sidebar.classList.contains('hidden')) {
        sidebar.classList.remove('hidden');
        sidebar.style.transform = 'translateX(0)';
        sidebar.style.position = 'fixed';
        if (overlay) overlay.classList.add('active');
    } else {
        sidebar.classList.add('hidden');
        sidebar.style.transform = 'translateX(-100%)';
        if (overlay) overlay.classList.remove('active');
    }
};

window.closeSidebarMobile = function() {
    const sidebar = document.querySelector('.functoweb-sidebar');
    const overlay = document.querySelector('.functoweb-sidebar-overlay');
    if (sidebar) sidebar.classList.add('hidden');
    if (overlay) overlay.classList.remove('active');
};

window.toggleNavGroup = function(button) {
    button.parentElement.classList.toggle('active');
};

window.toggleSubgroup = function(button) {
    button.parentElement.classList.toggle('active');
};

let sidebarHidden = false;
let hiddenAtWidth = null;

function hideSidebar() {
    const sidebar = document.querySelector('.functoweb-sidebar');
    const toggle = document.querySelector('.functoweb-sidebar-mobile-toggle');
    const main = document.querySelector('.functoweb-main');
    
    if (!sidebar || sidebarHidden) return;
    
    hiddenAtWidth = window.innerWidth;
    sidebar.classList.add('hidden');
    sidebar.style.transform = 'translateX(-100%)';
    sidebar.style.position = 'fixed';
    if (toggle) toggle.style.display = 'flex';
    if (main) main.style.marginLeft = '0';
    sidebarHidden = true;
}

function showSidebar() {
    const sidebar = document.querySelector('.functoweb-sidebar');
    const toggle = document.querySelector('.functoweb-sidebar-mobile-toggle');
    const main = document.querySelector('.functoweb-main');
    
    if (!sidebar || !sidebarHidden) return;
    
    sidebar.classList.remove('hidden');
    sidebar.style.transform = '';
    sidebar.style.position = '';
    if (toggle) toggle.style.display = 'none';
    if (main) main.style.marginLeft = '';
    sidebarHidden = false;
    hiddenAtWidth = null;
}

function checkSidebarOverlap() {
    const sidebar = document.querySelector('.functoweb-sidebar');
    const container = document.querySelector('.functoweb-container');
    
    if (!sidebar || !container) return;
    
    const currentWidth = window.innerWidth;
    
    if (sidebarHidden) {
        if (hiddenAtWidth && currentWidth > hiddenAtWidth + 50) {
            showSidebar();
        }
    } else {
        const sidebarRect = sidebar.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();
        const gap = containerRect.left - sidebarRect.right;
        
        if (gap < 10) {
            hideSidebar();
        }
    }
}

document.addEventListener('click', function(event) {
    if (event.target.classList.contains('functoweb-nav-link')) {
        if (sidebarHidden) {
            closeSidebarMobile();
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.functoweb-sidebar');
    const toggle = document.querySelector('.functoweb-sidebar-mobile-toggle');
    
    if (sidebar) {
        document.body.classList.add('has-sidebar');
    }
    
    if (toggle) toggle.style.display = 'none';
    
    checkSidebarOverlap();
});

window.addEventListener('load', checkSidebarOverlap);
window.addEventListener('resize', checkSidebarOverlap);