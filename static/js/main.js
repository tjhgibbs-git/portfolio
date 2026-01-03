document.addEventListener('DOMContentLoaded', function() {
    // Dark mode functionality
    const initTheme = () => {
        // Check for saved theme preference or default to system preference
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
        }

        updateThemeToggle();
    };

    const updateThemeToggle = () => {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const icon = themeToggle.querySelector('.theme-icon');
            const text = themeToggle.querySelector('.theme-text');

            if (currentTheme === 'dark') {
                icon.textContent = '☀️';
                text.textContent = 'Light Mode';
            } else {
                icon.textContent = '🌙';
                text.textContent = 'Dark Mode';
            }
        }
    };

    const toggleTheme = () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeToggle();
    };

    // Initialize theme on page load
    initTheme();

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            updateThemeToggle();
        }
    });

    // Add theme toggle event listener
    const themeToggleBtn = document.getElementById('theme-toggle');
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', toggleTheme);
    }

    // Mobile menu toggle
    const menuToggle = document.querySelector('.mobile-toggle');
    const navMenu = document.getElementById('nav-menu');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            navMenu.classList.toggle('active');
        });

        // Close menu when clicking a nav link
        navMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function() {
                navMenu.classList.remove('active');
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('nav') && !event.target.closest('.mobile-toggle') && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
            }
        });
    }
    
    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80, // Account for fixed header
                    behavior: 'smooth'
                });
                
                // Close mobile menu if open
                if (navMenu.classList.contains('active')) {
                    navMenu.classList.remove('active');
                }
            }
        });
    });
    
    // Animate elements on scroll
    const animateElements = function() {
        const skillCards = document.querySelectorAll('.skill-card');
        const projectCards = document.querySelectorAll('.project-card');
        
        const isInViewport = (element) => {
            const rect = element.getBoundingClientRect();
            return (
                rect.top <= (window.innerHeight || document.documentElement.clientHeight) * 0.8 &&
                rect.bottom >= 0
            );
        };
        
        // Animate skill cards
        skillCards.forEach((card, index) => {
            if (isInViewport(card)) {
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            }
        });
        
        // Animate project cards
        projectCards.forEach((card, index) => {
            if (isInViewport(card)) {
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            }
        });
    };
    
    // Set initial opacity and transform for animation elements
    document.querySelectorAll('.skill-card, .project-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    });
    
    // Run animations on load and scroll
    window.addEventListener('load', animateElements);
    window.addEventListener('scroll', animateElements);
    
    // Removed fadeIn effect on main element to prevent stacking context issues with header
});
