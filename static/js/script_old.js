document.addEventListener('DOMContentLoaded', function () {
    const maxProducts = 3;


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
    const removeProductBtn = document.querySelectorAll('.remove-product');
    const cards = document.querySelectorAll(".product-card");

    addProductBtn?.addEventListener('click', function () {
        for (const card of cards) {
            if (card.style.display === "none") {
                card.style.display = "block";
                card.querySelector('input[name$="-active"]').value = "1";
                break;
            }
        }

        updateAddButton();
    });

    removeProductBtn.forEach(button => {
        button.addEventListener('click', function () {
            const card = this.closest('.product-card');

            // clear fields
            card.querySelectorAll("input, textarea, select").forEach(field => {
                if (field.type === "file") {
                    field.value = "";
                }
                else if (field.tagName === "SELECT") {
                    field.selectedIndex = 0;
                }
                else {
                    field.value = "";
                }
            });

            card.querySelector('input[name$="-active"]').value = "0";

            card.style.display = "none";
            updateAddButton();
        });
    });

    function getVisibleProductCards() {
        return Array.from(cards).filter(card => card.style.display !== "none").length;
    }

    function updateAddButton() {
        const displayedCards = getVisibleProductCards();
        if (displayedCards >= maxProducts) {
            addProductBtn.style.display = "none";
            return;
        }
        addProductBtn.style.display = "inline-block";
    }

    // initial call to set add products button state
    updateAddButton();
});
