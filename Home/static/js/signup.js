

const roleSelect =
            document.getElementById(
                "id_role"
            );
const imageContainer =
            document.getElementById(
                "profile-image-container"
            );

function toggleImageField() {

            if (
                roleSelect.value ===
                "Student"
            ) {

                imageContainer.style.display =
                    "block";

            } else {

                imageContainer.style.display =
                    "none";
            }
        }

toggleImageField();

roleSelect.addEventListener(
            "change",
            toggleImageField
        );
 