document.addEventListener('DOMContentLoaded', function () {
    const MAX_PRODUCTS = 3;

    // Hide flash messages
    setTimeout(function () {
        let alerts = document.querySelectorAll(".alert");
        alerts.forEach(function (alert) {
            let bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 3500);

    const deleteModal = document.getElementById('deleteUserModal');

    deleteModal?.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;

        const userId = button.getAttribute('data-user-id');
        const username = button.getAttribute('data-username');

        const form = document.getElementById('deleteUserForm');
        form.action = `/users/delete/${userId}`;

        document.getElementById('modalUsername').textContent = username;
    });


    const addProductBtn = document.getElementById('add-product-btn');
    const container = document.getElementById("products-container");
    const template = document.getElementById("product-template");

    addProductBtn?.addEventListener('click', function () {
        const container = getContainer();
        const activeCardsCount = container.querySelectorAll(".product-card").length;

        console.log("ACTIVE CARDS COUNT: ", activeCardsCount)

        if (activeCardsCount >= MAX_PRODUCTS) return;

        const totalCards = container.querySelectorAll(".product-card").length;
        // Clone template content
        const html = template.innerHTML.replace(/__index__/g, totalCards);

        // Insert the new template
        container.insertAdjacentHTML("beforeend", html);

        toggleAddButton();
    });

    container?.addEventListener("click", function (e) {
        if (!e.target.classList.contains("remove-product")) return;

        const card = e.target.closest(".product-card");
        if (!card) return;

        card.remove();
        reindex();
        toggleAddButton();
    });

    function reindex() {
        const cards = container.querySelectorAll(".product-card");

        cards.forEach((card, index) => {
            // update card index
            card.dataset.index = index;

            // Grab all fields
            const fields = card.querySelectorAll("[data-field]");

            // Set the proper field name
            fields.forEach(field => {
                const fieldName = field.dataset.field;
                field.name = `products-${index}-${fieldName}`;
            });

        });
    }

    function toggleAddButton() {
        const container = getContainer();
        const addProductBtn = document.getElementById('add-product-btn');
        if (!container || !addProductBtn) return;

        const count = container.querySelectorAll(
            ".product-card:not(.is-deleted)"
        ).length;

        console.log("COUNT", count)

        if (count >= MAX_PRODUCTS) {
            addProductBtn.style.display = "none";
        }
        else {
            addProductBtn.style.display = "inline-block";
        }
    }

    function getContainer() {
        return document.getElementById("products-container");
    }

    // initial call to set add products button state
    toggleAddButton();

});
