const CART_KEY = "brewCafeCart";

function getCheckoutCart() {
    try {
        const cart = JSON.parse(
            localStorage.getItem(CART_KEY) || "[]"
        );

        if (!Array.isArray(cart)) {
            return [];
        }

        return cart.filter(item =>
            typeof item.name === "string" &&
            Number.isFinite(Number(item.price)) &&
            Number(item.price) >= 0 &&
            Number.isInteger(Number(item.quantity)) &&
            Number(item.quantity) > 0
        ).map(item => ({
            name: item.name,
            price: Number(item.price),
            quantity: Number(item.quantity)
        }));
    } catch {
        return [];
    }
}

function formatMoney(amount) {
    return "₹" + amount.toLocaleString("en-IN");
}

function renderCheckout() {
    const itemsContainer =
        document.getElementById("checkoutItems");

    if (!itemsContainer) return;

    const cart = getCheckoutCart();

    itemsContainer.replaceChildren();

    let total = 0;

    cart.forEach(item => {
        const subtotal = item.price * item.quantity;
        total += subtotal;

        const row = document.createElement("div");
        row.className = "checkout-item";

        const details = document.createElement("div");

        const name = document.createElement("div");
        name.className = "checkout-item-name";
        name.textContent = item.name;

        const quantity = document.createElement("div");
        quantity.className = "checkout-item-detail";
        quantity.textContent =
            `${item.quantity} × ${formatMoney(item.price)}`;

        const price = document.createElement("strong");
        price.textContent = formatMoney(subtotal);

        details.append(name, quantity);
        row.append(details, price);

        itemsContainer.appendChild(row);
    });

    document.getElementById("emptyCheckout").hidden =
        cart.length > 0;

    document.getElementById("placeOrderButton").disabled =
        cart.length === 0;

    document.getElementById("checkoutSubtotal").textContent =
        formatMoney(total);

    document.getElementById("checkoutTotal").textContent =
        formatMoney(total);

    document.getElementById("year").textContent =
        new Date().getFullYear();
}

document.addEventListener("DOMContentLoaded", () => {
    renderCheckout();

    const form = document.getElementById("checkoutForm");
    const button = document.getElementById("placeOrderButton");

    form.addEventListener("submit", async event => {
        event.preventDefault();

        const cart = getCheckoutCart();

        if (cart.length === 0) {
            alert("Your cart is empty. Please add items first.");
            return;
        }

        if (!form.reportValidity()) {
            return;
        }

        const customer = {
            name: document.getElementById("customerName").value.trim(),
            phone: document.getElementById("phone").value.trim(),
            address: document.getElementById("address").value.trim()
        };

        if (!customer.name || !customer.phone || !customer.address) {
            alert("Please fill in all delivery details.");
            return;
        }

        button.disabled = true;
        button.textContent = "Placing Order...";

        try {
            const response = await fetch("/place-order", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    customer: customer,
                    items: cart.map(item => ({
                        name: item.name,
                        quantity: item.quantity
                    }))
                })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(
                    result.error || "Unable to place your order."
                );
            }

            sessionStorage.setItem(
                "brewCafeSavedOrder",
                JSON.stringify({
                    order_reference: result.order_reference,
                    total: result.total
                })
            );

            localStorage.removeItem(CART_KEY);

            window.location.href =
                "/order-success?reference=" +
                encodeURIComponent(result.order_reference);

        } catch (error) {
            alert(
                error.message ||
                "Something went wrong. Please try again."
            );

            button.disabled = false;
            button.textContent = "Place Order ☕";
        }
    });
});