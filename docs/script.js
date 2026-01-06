// Real-time Financial Analytics Platform - Website JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
    }
    
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                // Close mobile menu if open
                if (navMenu && navMenu.classList.contains('active')) {
                    navMenu.classList.remove('active');
                    hamburger.classList.remove('active');
                }
            }
        });
    });
    
    // Navbar background change on scroll
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 100) {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            navbar.style.backdropFilter = 'blur(10px)';
        } else {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        }
    });
    
    // Intersection Observer for animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    document.querySelectorAll('.overview-card, .feature-card, .arch-component, .step').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Copy code functionality
    document.querySelectorAll('.code-block').forEach(block => {
        const button = document.createElement('button');
        button.className = 'copy-button';
        button.innerHTML = '<i class="fas fa-copy"></i>';
        button.title = 'Copy code';
        
        button.addEventListener('click', function() {
            const code = block.querySelector('code').textContent;
            navigator.clipboard.writeText(code).then(function() {
                button.innerHTML = '<i class="fas fa-check"></i>';
                button.style.color = '#10b981';
                setTimeout(() => {
                    button.innerHTML = '<i class="fas fa-copy"></i>';
                    button.style.color = '';
                }, 2000);
            });
        });
        
        block.style.position = 'relative';
        block.appendChild(button);
    });
    
    // Add copy button styles
    const style = document.createElement('style');
    style.textContent = `
        .copy-button {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: rgba(255, 255, 255, 0.1);
            border: none;
            color: #e2e8f0;
            padding: 0.5rem;
            border-radius: 0.25rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .copy-button:hover {
            background: rgba(255, 255, 255, 0.2);
        }
    `;
    document.head.appendChild(style);
    
    // Demo video play button
    const playButton = document.querySelector('.play-button');
    if (playButton) {
        playButton.addEventListener('click', function() {
            // In a real implementation, you would show a modal with the actual demo video
            alert('Demo video would play here! For now, try running the application locally to see the live demo.');
        });
    }
    
    // Animate statistics counters
    function animateCounters() {
        const counters = document.querySelectorAll('.stat-number');
        
        counters.forEach(counter => {
            const target = counter.textContent;
            const isNumber = !isNaN(parseInt(target.replace(/[^\d]/g, '')));
            
            if (isNumber) {
                const value = parseInt(target.replace(/[^\d]/g, ''));
                const increment = value / 100;
                let current = 0;
                
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= value) {
                        current = value;
                        clearInterval(timer);
                    }
                    counter.textContent = target.replace(value, Math.floor(current).toLocaleString());
                }, 20);
            }
        });
    }
    
    // Trigger counter animation when hero section is visible
    const heroSection = document.querySelector('.hero');
    if (heroSection) {
        const heroObserver = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounters();
                    heroObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        heroObserver.observe(heroSection);
    }
    
    // Tech stack item hover effects
    document.querySelectorAll('.tech-item').forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(10px) scale(1.05)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0) scale(1)';
        });
    });
    
    // Service link hover effects
    document.querySelectorAll('.service-link').forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Add loading animation for GitHub links
    document.querySelectorAll('a[href*="github.com"]').forEach(link => {
        link.addEventListener('click', function(e) {
            const icon = this.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-spinner fa-spin';
                setTimeout(() => {
                    icon.className = 'fab fa-github';
                }, 1000);
            }
        });
    });
    
    // Lazy loading for images (if any are added later)
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    observer.unobserve(img);
                }
            });
        });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }
    
    // Add subtle parallax effect to hero background
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const hero = document.querySelector('.hero');
        if (hero && scrolled < hero.offsetHeight) {
            hero.style.transform = `translateY(${scrolled * 0.5}px)`;
        }
    });
    
    // Update copyright year
    const currentYear = new Date().getFullYear();
    const copyrightElement = document.querySelector('.footer-bottom p');
    if (copyrightElement) {
        copyrightElement.textContent = copyrightElement.textContent.replace('2026', currentYear);
    }
    
    // Add keyboard navigation support
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            // Close mobile menu if open
            if (navMenu && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                hamburger.classList.remove('active');
            }
        }
    });
    
    // Initialize AOS (Animate On Scroll) if available
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
            once: true,
            offset: 100
        });
    }
    
    console.log('Real-time Financial Analytics Platform website loaded successfully!');
    console.log('🚀 Ready to showcase your skills to recruiters!');
    
    // Initialize interactive demo
    initializeDemo();
});

// Interactive Demo Functions
function openDemoModal() {
    const modal = document.getElementById('demoModal');
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    startDemoAnimation();
}

function closeDemoModal() {
    const modal = document.getElementById('demoModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
    stopDemoAnimation();
}

let demoInterval;
let chartData = [];

function initializeDemo() {
    // Close modal when clicking outside
    window.onclick = function(event) {
        const modal = document.getElementById('demoModal');
        if (event.target === modal) {
            closeDemoModal();
        }
    };
    
    // Chart button interactions
    document.querySelectorAll('.demo-chart-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.demo-chart-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            updateChart(this.dataset.symbol);
        });
    });
    
    // Initialize chart data
    generateChartData();
}

function startDemoAnimation() {
    // Update stock prices every 2 seconds
    demoInterval = setInterval(() => {
        updateStockPrices();
        updateChart();
    }, 2000);
    
    // Initial chart draw
    drawChart();
}

function stopDemoAnimation() {
    if (demoInterval) {
        clearInterval(demoInterval);
    }
}

function updateStockPrices() {
    const stocks = ['aapl', 'googl', 'tsla', 'msft'];
    const baseprices = { aapl: 150, googl: 2785, tsla: 245, msft: 342 };
    
    stocks.forEach(stock => {
        // Generate realistic price movements
        const changePercent = (Math.random() - 0.5) * 4; // -2% to +2%
        const newPrice = baseprices[stock] * (1 + changePercent / 100);
        const volume = (Math.random() * 2 + 0.5).toFixed(1) + 'M';
        
        // Update UI
        const priceEl = document.getElementById(`${stock}-price`);
        const changeEl = document.getElementById(`${stock}-change`);
        const volumeEl = document.getElementById(`${stock}-volume`);
        
        if (priceEl) priceEl.textContent = `$${newPrice.toFixed(2)}`;
        if (changeEl) {
            changeEl.textContent = `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%`;
            changeEl.className = changePercent >= 0 ? 'demo-positive' : 'demo-negative';
        }
        if (volumeEl) volumeEl.textContent = volume;
    });
}

function generateChartData() {
    chartData = [];
    const basePrice = 150;
    
    for (let i = 0; i < 50; i++) {
        const variation = (Math.random() - 0.5) * 10;
        chartData.push({
            x: i * 8,
            y: 100 + variation + Math.sin(i / 5) * 20
        });
    }
}

function drawChart() {
    const svg = document.getElementById('demo-chart-svg');
    const line = document.getElementById('demo-chart-line');
    const dot = document.getElementById('demo-chart-dot');
    
    if (!svg || !line || !dot) return;
    
    const svgRect = svg.getBoundingClientRect();
    const width = svgRect.width;
    const height = 200;
    
    // Generate path
    let pathData = '';
    chartData.forEach((point, i) => {
        const x = (point.x / 400) * width;
        const y = height - (point.y / 200) * height;
        pathData += i === 0 ? `M ${x} ${y}` : ` L ${x} ${y}`;
    });
    
    line.setAttribute('d', pathData);
    
    // Position dot at the end
    if (chartData.length > 0) {
        const lastPoint = chartData[chartData.length - 1];
        const x = (lastPoint.x / 400) * width;
        const y = height - (lastPoint.y / 200) * height;
        dot.setAttribute('cx', x);
        dot.setAttribute('cy', y);
    }
}

function updateChart(symbol = 'AAPL') {
    // Add new data point
    if (chartData.length > 50) {
        chartData.shift();
    }
    
    const lastY = chartData[chartData.length - 1].y;
    const newY = lastY + (Math.random() - 0.5) * 10;
    
    chartData.forEach((point, i) => {
        point.x = i * 8;
    });
    
    chartData.push({
        x: (chartData.length - 1) * 8,
        y: Math.max(50, Math.min(150, newY))
    });
    
    drawChart();
}