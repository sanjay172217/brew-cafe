const CART_KEY = "brewCafeCart";

const productImages = {
    "Cappuccino": "https://images.unsplash.com/photo-1534778101976-62847782c213?auto=format&fit=crop&w=200&q=80",
    "Latte": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=200&q=80",
    "Americano": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?auto=format&fit=crop&w=200&q=80",
    "Masala Tea": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=200&q=80",
    "Iced Coffee": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=200&q=80",
    "Butter Croissant": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=200&q=80",
    "Veg Sandwich": "https://images.unsplash.com/photo-1553909489-cd47e0ef937f?auto=format&fit=crop&w=200&q=80",
    "Chocolate Cake": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=200&q=80"
};

function readCart() {
    try {
        const saved = JSON.parse(localStorage.getItem(CART_KEY) || "[]");

        if (!Array.isArray(saved)) {
            return [];
        }

        return saved.filter(item =>
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

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

function money(amount) {
    return "₹" + amount.toLocaleString("en-IN");
}

function renderCart() {
    const container = document.getElementById("cartItems");

    // The cart script is also safe to load on pages without cart elements.
    if (!container) {
        return;
    }

    const cart = readCart();
    container.replaceChildren();

    const emptyCart = document.getElementById("emptyCart");
    const checkoutButton = document.getElementById("checkoutButton");

    emptyCart.hidden = cart.length > 0;
    checkoutButton.disabled = cart.length === 0;

    let totalQuantity = 0;
    let subtotal = 0;

    cart.forEach((item, index) => {
        totalQuantity += item.quantity;
        subtotal += item.price * item.quantity;

        const row = document.createElement("article");
        row.className = "cart-item";

        const img = document.createElement("img");
        img.className = "cart-item-image";
        img.src = productImages[item.name] || "";
        img.alt = item.name;

        const details = document.createElement("div");
        details.className = "cart-item-details";

        const name = document.createElement("h3");
        name.textContent = item.name;

        const price = document.createElement("div");
        price.className = "cart-item-price";
        price.textContent = money(item.price) + " each";

        const controls = document.createElement("div");
        controls.className = "quantity-controls";

        const decrease = document.createElement("button");
        decrease.type = "button";
        decrease.textContent = "−";
        decrease.setAttribute("aria-label", "Decrease quantity");

        decrease.addEventListener("click", () => {
            const updated = readCart();

            if (!updated[index]) return;

            updated[index].quantity -= 1;

            if (updated[index].quantity <= 0) {
                updated.splice(index, 1);
            }

            saveCart(updated);
            renderCart();
        });

        const quantity = document.createElement("span");
        quantity.className = "quantity-number";
        quantity.textContent = item.quantity;

        const increase = document.createElement("button");
        increase.type = "button";
        increase.textContent = "+";
        increase.setAttribute("aria-label", "Increase quantity");

        increase.addEventListener("click", () => {
            const updated = readCart();

            if (!updated[index]) return;

            updated[index].quantity += 1;
            saveCart(updated);
            renderCart();
        });

        controls.append(decrease, quantity, increase);
        details.append(name, price, controls);

        const end = document.createElement("div");
        end.className = "cart-item-end";

        const lineTotal = document.createElement("div");
        lineTotal.className = "cart-item-total";
        lineTotal.textContent = money(item.price * item.quantity);

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "remove-item";
        remove.textContent = "Remove";

        remove.addEventListener("click", () => {
            const updated = readCart();
            updated.splice(index, 1);
            saveCart(updated);
            renderCart();
        });

        end.append(lineTotal, remove);
        row.append(img, details, end);
        container.appendChild(row);
    });

    document.getElementById("itemCount").textContent = totalQuantity;
    document.getElementById("subtotal").textContent = money(subtotal);
    document.getElementById("total").textContent = money(subtotal);

    const year = document.getElementById("year");

    if (year) {
        year.textContent = new Date().getFullYear();
    }
}

document.addEventListener("DOMContentLoaded", () => {
    renderCart();

    const checkoutButton = document.getElementById("checkoutButton");

    if (checkoutButton) {
        checkoutButton.addEventListener("click", () => {
            if (readCart().length === 0) {
                alert("Your cart is empty. Please add some delicious items!");
                return;
            }

            window.location.href = "/order";
        });
    }
});