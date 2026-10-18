const menuToggle = document.getElementById("menuToggle");
const navLinks = document.getElementById("navLinks");
const cartNotice = document.getElementById("cartNotice");

let cart = JSON.parse(localStorage.getItem("brewCafeCart") || "[]");

if (menuToggle && navLinks) {
    menuToggle.addEventListener("click", () => {
        const isOpen = navLinks.classList.toggle("open");
        menuToggle.setAttribute("aria-expanded", String(isOpen));
    });

    navLinks.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", () => {
            navLinks.classList.remove("open");
            menuToggle.setAttribute("aria-expanded", "false");
        });
    });
}

document.querySelectorAll(".add-button").forEach(button => {
    button.addEventListener("click", () => {
        const name = button.dataset.item;
        const price = Number(button.dataset.price);

        const existingItem = cart.find(item => item.name === name);

        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cart.push({
                name,
                price,
                quantity: 1
            });
        }

        localStorage.setItem("brewCafeCart", JSON.stringify(cart));

        const totalItems = cart.reduce(
            (total, item) => total + item.quantity,
            0
        );

        cartNotice.textContent =
            `${name} added! Your cart has ${totalItems} item(s).`;

        button.innerHTML = "Added ✓";

        setTimeout(() => {
            button.innerHTML = 'Add to Order <span>+</span>';
        }, 1200);
    });
});

const year = document.getElementById("year");

if (year) {
    year.textContent = new Date().getFullYear();
}