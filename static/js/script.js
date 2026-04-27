document.addEventListener('DOMContentLoaded', function () {
    const MAX_PRODUCTS = 3;

    // Hide flash messages
    setTimeout(function () {
        let alerts = document.querySelectorAll(".alert");
        alerts.forEach(function (alert) {
            let bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 3500); // 2500 ms = 2.5 seconds

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
    const cards = document.querySelectorAll(".product-card");
    const template = document.getElementById("product-template");

    addProductBtn?.addEventListener('click', function () {
        const count = container.children.length;

        if (count >= MAX_PRODUCTS) return;

        // Clone template content
        const html = template.innerHTML.replace(/__index__/g, count);


        // Insert the new template
        container.insertAdjacentHTML("beforeend", html);

        toggleAddButton();
    });

    container.addEventListener("click", function (e) {
        if (e.target.classList.contains("remove-product")) {
            e.target.closest(".product-card").remove();

            reindex();
            toggleAddButton();
        }
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
        const count = container.children.length;

        if (count >= MAX_PRODUCTS) {
            addProductBtn.style.display = "none";
        }
        else {
            addProductBtn.style.display = "inline-block";
        }
    }

    // initial call to set add products button state
    toggleAddButton();

});
