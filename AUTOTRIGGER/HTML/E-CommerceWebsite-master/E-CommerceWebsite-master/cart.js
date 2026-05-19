
// Initialize variables
let cartContainer = document.getElementById('cartContainer');
let totalAmount = 0;
let cartItems = [];

// Function to render the dynamic cart section with + and - buttons for quantity
function dynamicCartSection(ob, itemCounter, itemId) {
    let boxDiv = document.createElement('div');
    boxDiv.classList.add('cart-item');
    boxDiv.id = `item-${itemId}`;

    let boxImg = document.createElement('img');
    boxImg.src = ob.preview;
    boxDiv.appendChild(boxImg);

    let boxDetails = document.createElement('div');
    boxDetails.classList.add('item-details');

    let boxh3 = document.createElement('h3');
    boxh3.textContent = `${ob.name} × ${itemCounter}`;
    boxDetails.appendChild(boxh3);

    let boxh4 = document.createElement('h4');
    boxh4.textContent = `Amount: Rs ${ob.price * itemCounter}`;
    boxDetails.appendChild(boxh4);

    // Add + and - buttons for quantity adjustment
    let quantityDiv = document.createElement('div');
    quantityDiv.classList.add('quantity-controls');
    let minusBtn = document.createElement('button');
    minusBtn.textContent = '-';
    minusBtn.id = `minus-${itemId}`;
    minusBtn.onclick = function () {
        updateQuantity(itemId, -1, ob.price);
    };

    let quantityDisplay = document.createElement('span');
    quantityDisplay.id = `quantity-${itemId}`;
    quantityDisplay.textContent = itemCounter;

    let plusBtn = document.createElement('button');
    plusBtn.textContent = '+';
    plusBtn.onclick = function () {
        updateQuantity(itemId, 1, ob.price);
    };

    // Create delete button
    let deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Delete';
    deleteBtn.id = `delete-${itemId}`;
    deleteBtn.style.display = 'none'; // Initially hidden
    deleteBtn.onclick = function () {
        deleteItem(itemId, ob.price);
    };

    quantityDiv.appendChild(minusBtn);
    quantityDiv.appendChild(quantityDisplay);
    quantityDiv.appendChild(plusBtn);
    quantityDiv.appendChild(deleteBtn);  // Append Delete Button
    boxDetails.appendChild(quantityDiv);

    boxDiv.appendChild(boxDetails);
    cartContainer.appendChild(boxDiv);
}

// Function to update the total amount and item quantity
function updateQuantity(itemId, change, price) {
    let quantityElement = document.getElementById(`quantity-${itemId}`);
    let quantity = parseInt(quantityElement.textContent);

    // Update quantity and ensure it stays >= 1
    quantity += change;
    if (quantity < 1) {
        quantity = 1;
    }
    quantityElement.textContent = quantity;

    // Disable the minus button when quantity is 1
    let minusBtn = document.getElementById(`minus-${itemId}`);
    let deleteBtn = document.getElementById(`delete-${itemId}`);
    if (quantity === 1) {
        minusBtn.disabled = true;
        deleteBtn.style.display = 'inline-block'; // Show delete button
    } else {
        minusBtn.disabled = false;
        deleteBtn.style.display = 'none'; // Hide delete button
    }

    // Update total amount
    totalAmount += change * price;
    amountUpdate();
}

// Function to delete an item from the cart
function deleteItem(itemId, price) {
    let itemDiv = document.getElementById(`item-${itemId}`);
    itemDiv.remove(); // Remove the item from the cart display

    // Adjust the total amount
    let quantity = parseInt(document.getElementById(`quantity-${itemId}`).textContent);
    totalAmount -= price * quantity;
    amountUpdate();
}

// Function to update the total amount in the cart
function amountUpdate() {
    let subtotal = totalAmount;
    let taxAmount = subtotal * 0.18; // 18% tax
    let discountAmount = parseFloat(document.getElementById('discountAmount').textContent.replace('Rs ', '')) || 0;
    let total = subtotal + taxAmount - discountAmount;

    // Update UI with new values
    document.getElementById('subtotalAmount').textContent = `Rs ${subtotal.toFixed(2)}`;
    document.getElementById('taxAmount').textContent = `Rs ${taxAmount.toFixed(2)}`;
    document.getElementById('totalPrice').textContent = `Rs ${total.toFixed(2)}`;
}

// Function to apply a discount code (example: 10% off)
function applyDiscount() {
    let discountCode = document.getElementById('discountCode').value;
    let discountAmount = 0;

    if (discountCode === "DISCOUNT10") {
        discountAmount = totalAmount * 0.10; // Apply 10% discount
        alert("Discount applied!");
    } else {
        alert("Invalid discount code.");
    }

    // Update discount UI
    document.getElementById('discountAmount').textContent = `Rs ${discountAmount.toFixed(2)}`;
    amountUpdate();
}

// Function to checkout (expandable for payment integration)
function checkout() {
    alert("Proceeding to checkout!");
    // In real use, you would send the cart details to the server here.
}

// Load cart items and render dynamically
let httpRequest = new XMLHttpRequest();
httpRequest.onreadystatechange = function () {
    if (this.readyState === 4 && this.status === 200) {
        let contentTitle = JSON.parse(this.responseText);
        let cart = document.cookie.split(',');
        let itemCount = Number(cart[1].split('=')[1]);
        document.getElementById('totalItem').textContent = `Total Items: ${itemCount}`;

        let itemIds = cart[0].split('=')[1].split(" ");
        let itemQuantities = {};

        // Calculate item quantities and render the cart
        itemIds.forEach(id => {
            itemQuantities[id] = (itemQuantities[id] || 0) + 1;
        });

        itemIds.forEach(id => {
            if (itemQuantities[id]) {
                let item = contentTitle[id - 1]; // Adjust to 0-based index
                dynamicCartSection(item, itemQuantities[id], id);
                totalAmount += item.price * itemQuantities[id];
                itemQuantities[id] = 0; // Mark this item as processed
            }
        });

        amountUpdate();
    }
};

httpRequest.open('GET', 'https://5d76bf96515d1a0014085cf9.mockapi.io/product', true);
httpRequest.send();