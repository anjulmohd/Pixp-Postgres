document.addEventListener('DOMContentLoaded', function() {
    // Product variant update functionality
    const variantRadios = document.querySelectorAll('input[name="variant_id"]');
    const productImage = document.getElementById('product-image');
    const productName = document.getElementById('product-name');
    const productPrice = document.getElementById('product-price');
    const productStock = document.getElementById('product-stock');
    const quantityInput = document.getElementById('quantity');
    const thumbnailContainer = document.querySelector('.thumbnail-container');
    
    function updateProductDetails(variant) {
        const imageSrc = variant.dataset.image;
        productImage.src = imageSrc;
        productName.textContent = variant.dataset.name;
        productPrice.textContent = variant.dataset.price;

        // Update thumbnail selection to highlight the current image
        const thumbnails = document.querySelectorAll('.thumbnail-image');
        let thumbnailFound = false;
        
        thumbnails.forEach(thumbnail => {
            if (thumbnail.dataset.mainImage === imageSrc) {
                thumbnail.classList.add('active');
                thumbnailFound = true;
            } else {
                thumbnail.classList.remove('active');
            }
        });

        // If the variant image isn't in the thumbnails, update the main product thumbnail
        if (!thumbnailFound) {
            // Get the first thumbnail (which is the main product image)
            const mainThumbnail = document.querySelector('.thumbnail-container .thumbnail-item:first-child img');
            if (mainThumbnail) {
                mainThumbnail.src = imageSrc;
                mainThumbnail.dataset.mainImage = imageSrc;
                mainThumbnail.classList.add('active');
            }
        }

        const stockQuantity = parseInt(variant.dataset.stock);
        if (stockQuantity > 10) {
            productStock.textContent = 'In Stock';
            productStock.className = 'stock-value in-stock';
        } else if (stockQuantity > 0) {
            productStock.textContent = `Low Stock (${stockQuantity} left)`;
            productStock.className = 'stock-value low-stock';
        } else {
            productStock.textContent = 'Out of Stock';
            productStock.className = 'stock-value out-of-stock';
        }

        quantityInput.max = stockQuantity;
        if (quantityInput.value > stockQuantity) {
            quantityInput.value = stockQuantity;
        }

        localStorage.setItem('selectedVariantId', variant.value);
    }

    variantRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.checked) {
                updateProductDetails(this);
            }
        });
    });

    function incrementQuantity() {
        let currentValue = parseInt(quantityInput.value);
        const maxValue = parseInt(quantityInput.max);
        if (currentValue < maxValue) {
            quantityInput.value = currentValue + 1;
        } else {
            alert(`You cannot add more than ${maxValue} items.`);
        }
    }

    function decrementQuantity() {
        let currentValue = parseInt(quantityInput.value);
        if (currentValue > 1) {
            quantityInput.value = currentValue - 1;
        }
    }

    const savedVariantId = localStorage.getItem('selectedVariantId');
    if (savedVariantId) {
        const savedVariant = document.querySelector(`input[name="variant_id"][value="${savedVariantId}"]`);
        if (savedVariant) {
            savedVariant.checked = true;
            updateProductDetails(savedVariant);
        }
    } else {
        const baseVariant = document.querySelector('input[name="variant_id"][value=""]');
        if (baseVariant) {
            baseVariant.checked = true;
            updateProductDetails(baseVariant);
        }
    }

    document.querySelector('.plus-btn').addEventListener('click', incrementQuantity);
    document.querySelector('.minus-btn').addEventListener('click', decrementQuantity);

   
    // Thumbnail and Zoom functionality
    const mainImage = document.getElementById('product-image');
    const thumbnailImages = document.querySelectorAll('.thumbnail-image');
    let isZoomed = false;
    let zoomContainer = null;

    thumbnailImages.forEach(thumbnail => {
        thumbnail.addEventListener('click', function () {
            const newImageSrc = this.getAttribute('data-main-image');
            mainImage.setAttribute('src', newImageSrc);
            
            // Update active state on thumbnails
            thumbnailImages.forEach(img => img.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // Create zoom container
    function createZoomContainer() {
        if (zoomContainer) return;
        
        zoomContainer = document.createElement('div');
        zoomContainer.className = 'image-zoom-container';
        zoomContainer.style.position = 'absolute';
        zoomContainer.style.top = '0';
        zoomContainer.style.left = '0';
        zoomContainer.style.width = '100%';
        zoomContainer.style.height = '100%';
        zoomContainer.style.overflow = 'hidden';
        zoomContainer.style.zIndex = '5';
        zoomContainer.style.display = 'none';
        
        const zoomedImage = document.createElement('img');
        zoomedImage.id = 'zoomed-image';
        zoomedImage.src = mainImage.src;
        zoomedImage.style.position = 'absolute';
        zoomedImage.style.transformOrigin = '0 0';
        zoomedImage.style.width = '100%';
        zoomedImage.style.height = '100%';
        
        zoomContainer.appendChild(zoomedImage);
        
        const imageContainer = document.querySelector('.main-image-container');
        imageContainer.style.position = 'relative';
        imageContainer.appendChild(zoomContainer);
    }

    // Fixed zoom functionality
    mainImage.addEventListener('mouseenter', function() {
        createZoomContainer();
        const zoomedImage = document.getElementById('zoomed-image');
        zoomedImage.src = mainImage.src;
        zoomContainer.style.display = 'block';
        isZoomed = true;
    });

    document.querySelector('.main-image-container').addEventListener('mousemove', function(e) {
        if (!isZoomed) return;
        
        const rect = this.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const scale = 2;
        const zoomedImage = document.getElementById('zoomed-image');
        
        const xPercent = x / rect.width;
        const yPercent = y / rect.height;
        
        const xPos = -1 * (xPercent * (zoomedImage.offsetWidth * scale - rect.width));
        const yPos = -1 * (yPercent * (zoomedImage.offsetHeight * scale - rect.height));
        
        zoomedImage.style.transform = `scale(${scale})`;
        zoomedImage.style.left = `${xPos}px`;
        zoomedImage.style.top = `${yPos}px`;
    });

    document.querySelector('.main-image-container').addEventListener('mouseleave', function() {
        if (zoomContainer) {
            zoomContainer.style.display = 'none';
        }
        isZoomed = false;
    });
});