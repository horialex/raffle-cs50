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

    // Treat form fields - to clean when defaults or not filled fields
    const form = document.querySelector("form");
    form.addEventListener("submit", function () {
        const defaultSort = form.dataset.defaultSort;
        const fields = form.querySelectorAll("input, select");

        fields.forEach(function (field) {
            const fieldName = field.name;
            const value = field.value.trim();

            // Do not send empty fields
            if (value === "") {
                field.disabled = true;
            }

            // Do not send default status
            if (fieldName === "status_filter" && value === "all") {
                field.disabled = true;
            }

            // Do not send default sort
            if (fieldName === "sort" && value === defaultSort) {
                field.disabled = true;
            }
            // Do not send default category TODO: Fix this when categories are added
            if (field.name === "category" && value === "") {
                field.disabled = true;
            }

            // Do not send default pagination
            if (fieldName === "page" && value === "1") {
                field.disabled = true;
            }
            if (fieldName === "per_page" && value === "6") {
                field.disabled = true;
            }
        });
    });

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


    // Header tabs active state
    document.querySelectorAll('.nav-tabs .nav-link').forEach(link => {
        link.addEventListener('click', function () {
            document.querySelectorAll('.nav-tabs .nav-link').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // More Filters chevron icon up-down
    const moreFiltersContainer = document.getElementById('moreFilters');
    const chevronIcon = document.getElementById('moreFiltersChevron')

    moreFiltersContainer?.addEventListener('show.bs.collapse', () => {
        chevronIcon.classList.remove('bi-chevron-down');
        chevronIcon.classList.add('bi-chevron-up');
    });

    moreFiltersContainer?.addEventListener('hide.bs.collapse', () => {
        chevronIcon.classList.remove('bi-chevron-up');
        chevronIcon.classList.add('bi-chevron-down');
    });

    const quantityInput = document.getElementById("quantity-input");
    const ticketCount = document.getElementById("ticket-count");
    const checkoutTotal = document.getElementById("checkout-total")


    quantityInput?.addEventListener("input", function () {
        const ticketPrice = parseFloat(quantityInput.dataset.price);
        const qty = quantityInput.value;
        ticketCount.textContent = qty;

        checkoutTotal.textContent = `$${(qty * ticketPrice).toFixed(0)}`;
    });




});
