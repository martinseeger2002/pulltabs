let pullTabImage, backImage, tabImage, ripImages = [], winImage;
let currentImage;
let button;
let icons = [];
let tabIndex;
let tabs = [
    { x: 5, y: 55, ripImage: 'rip1.png', removed: false },
    { x: 5, y: 140, ripImage: 'rip2.png', removed: false },
    { x: 5, y: 220, ripImage: 'rip3.png', removed: false }
];
const ASPECT_RATIO = 2 / 3; // Aspect ratio (width / height)

function preload() {
    pullTabImage = loadImage('./images/pulltab.png');
    backImage = loadImage('./images/back.png');
    tabImage = loadImage('./images/tab.png');
    ripImages[0] = loadImage('./images/rip1.png');
    ripImages[1] = loadImage('./images/rip2.png');
    ripImages[2] = loadImage('./images/rip3.png');
    winImage = loadImage('./images/win.png');
    for (let i = 1; i <= 7; i++) {
        icons[i] = loadImage(`./images/${i}.png`);
    }
}

function setup() {
    let canvasContainer = createDiv();
    canvasContainer.id('canvas-container');
    canvasContainer.style('position', 'relative');
    canvasContainer.style('display', 'inline-block');
    canvasContainer.style('overflow', 'hidden'); // Prevent scrollbars

    adjustCanvasSize();

    let canvas = createCanvas(width, height);
    canvas.parent(canvasContainer);

    // Get the tabIndex from the body attribute
    tabIndex = document.body.getAttribute('tabindex');

    // Apply styles to center the canvas
    document.body.style.display = 'flex';
    document.body.style.justifyContent = 'center';
    document.body.style.alignItems = 'center';
    document.body.style.height = '100vh';
    document.body.style.margin = '0';
    document.body.style.overflow = 'hidden'; // Prevent scrollbars

    // Create the button
    button = createButton('');
    button.size(width * 0.175, height * 0.167); // Adjust button size based on canvas size
    button.style('background-color', 'red');
    button.style('border', 'none');
    button.style('opacity', '0.0');
    button.style('position', 'absolute');
    button.style('top', '0px');
    button.style('left', '0px');
    button.mousePressed(switchImage);
    canvasContainer.child(button);

    currentImage = pullTabImage;
    background(255); // Set the background to white
}

function draw() {
    background(255);
    displayIcons();
    checkForWin(); // Check for win condition and display win image if needed behind tabs
    displayTabs();
    image(pullTabImage, 0, 0, width, height); // Always draw the pullTabImage

    displayRipImages(); // Display the rip images on top of pullTabImage
    
    if (currentImage === backImage) {
        image(backImage, 0, 0, width, height); // Draw backImage on top
    }
}

function switchImage() {
    if (currentImage === pullTabImage) {
        currentImage = backImage;
        button.size(width, height); // Make the button cover the entire canvas
    } else {
        currentImage = pullTabImage;
        button.size(width * 0.175, height * 0.167); // Reset the button size
    }
}

function displayIcons() {
    const startX = width * 0.11;  // X offset to start drawing icons
    const startY = height * 0.2;  // Y offset to start drawing icons
    const iconWidth = width * 0.25;
    const iconHeight = height * 0.167;
    const paddingX = width * 0.015;
    const paddingY = height * 0.11;

    for (let i = 0; i < 9; i++) {
        let iconIndex = parseInt(tabIndex[i]);
        if (iconIndex >= 1 && iconIndex <= 7) {
            let x = startX + (i % 3) * (iconWidth + paddingX);  // Calculate x position
            let y = startY + Math.floor(i / 3) * (iconHeight + paddingY);  // Calculate y position
            image(icons[iconIndex], x, y, iconWidth, iconHeight);
        }
    }
}

function displayTabs() {
    const tabWidth = width * 0.95;
    const tabHeight = height * 0.2;
    const positions = [
        { x: width * 0.025, y: height * 0.18 },
        { x: width * 0.025, y: height * 0.47 },
        { x: width * 0.025, y: height * 0.73 }
    ];

    for (let i = 0; i < positions.length; i++) {
        if (!tabs[i].removed) {
            image(tabImage, positions[i].x, positions[i].y, tabWidth, tabHeight);
        }
    }
}

function displayRipImages() {
    for (let i = 0; i < tabs.length; i++) {
        if (tabs[i].removed) {
            image(ripImages[i], 0, 0, width, height);
        }
    }
}

function checkForWin() {
    const winAspectRatio = 244 / 300;
    let winWidth, winHeight;

    // Calculate win image dimensions based on canvas size while maintaining aspect ratio
    if (width / height > winAspectRatio) {
        winHeight = height * 1.0; // Adjust the height multiplier as needed
        winWidth = winHeight * winAspectRatio;
    } else {
        winWidth = width * 1.0; // Adjust the width multiplier as needed
        winHeight = winWidth / winAspectRatio;
    }

    // Check first three digits
    if (tabIndex[0] === tabIndex[1] && tabIndex[1] === tabIndex[2]) {
        const x = (width - winWidth) / 2;
        const y = height * 1.0 + (height * 0.2) / 2 - (winHeight / 2);
        image(winImage, x, y, winWidth, winHeight);
    }

    // Check middle three digits
    if (tabIndex[3] === tabIndex[4] && tabIndex[4] === tabIndex[5]) {
        const x = (width - winWidth) / 2;
        const y = height * 0.44 + (height * 0.2) / 2 - (winHeight / 2);
        image(winImage, x, y, winWidth, winHeight);
    }

    // Check last three digits
    if (tabIndex[6] === tabIndex[7] && tabIndex[7] === tabIndex[8]) {
        const x = (width - winWidth) / 2;
        const y = height * 0.71 + (height * 0.2) / 2 - (winHeight / 2);
        image(winImage, x, y, winWidth, winHeight);
    }
}

function mousePressed() {
    for (let i = 0; i < tabs.length; i++) {
        let tab = tabs[i];
        let pos = {
            x: width * 0.025,
            y: height * 0.18 + i * (height * 0.29)
        };
        let tabWidth = width * 0.95;
        let tabHeight = height * 0.2;

        if (mouseX > pos.x && mouseX < pos.x + tabWidth && mouseY > pos.y && mouseY < pos.y + tabHeight) {
            tabs[i].removed = true;
        }
    }
}

function adjustCanvasSize() {
    let canvasContainer = document.querySelector('#canvas-container');
    let windowAspectRatio = windowWidth / windowHeight;

    if (windowAspectRatio > ASPECT_RATIO) {
        // Window is wider than the canvas aspect ratio
        height = windowHeight;
        width = height * ASPECT_RATIO;
    } else {
        // Window is taller than the canvas aspect ratio
        width = windowWidth;
        height = width / ASPECT_RATIO;
    }

    canvasContainer.style.width = `${width}px`;
    canvasContainer.style.height = `${height}px`;
}

function windowResized() {
    adjustCanvasSize();
    resizeCanvas(width, height);
    button.size(width * 0.175, height * 0.167); // Adjust button size on resize
}
