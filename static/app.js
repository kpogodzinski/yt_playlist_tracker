const LOADER = document.getElementById("loader-wrapper")
const POPUP = document.getElementById("popup")

document.querySelectorAll(".save-btn").forEach(button => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        const playlistId = button.dataset.id

        LOADER.style.display = "flex";
        button.textContent = "Saving...";

        fetch(`/save_playlist/${playlistId}`, { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                button.textContent = "Saved!";
                button.disabled = true;
            } else if (data.status === "exists") {
                button.textContent = "Already saved";
                button.disabled = true;
            }
        })
        .catch(err => {
            console.error(err);
            window.location.reload();
        })
        .finally(() => {
            LOADER.style.display = "none";
        })
    });
});

document.querySelectorAll(".rm-btn").forEach(button => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        const confirmed = confirm("Are you sure to remove this playlist?");
        if (!confirmed) return;

        const playlistId = button.dataset.id

        LOADER.style.display = "flex";
        button.textContent = "Removing...";

        fetch(`/remove_playlist/${playlistId}`, { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                button.textContent = "Removed!";
                button.disabled = true;
            } else {
                button.textContent = "Error";
            }
        })
        .catch(err => {
            console.error(err);
            window.location.reload();
        })
        .finally(() => {
            LOADER.style.display = "none";
        })
    });
});

document.querySelectorAll(".watch-btn").forEach(button => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        const videoId = button.dataset.video;

        LOADER.style.display = "flex";
        button.textContent = "Please wait...";

        fetch(`/watch_video/${videoId}`, { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.status === "watched") {
                button.textContent = "Watched";
                button.classList.add("watched");
            } else if (data.status === "unwatched") {
                button.textContent = "Not watched"
                button.classList.remove("watched")
            } else if (data.status === "not saved") {
                button.textContent = "Save the playlist first!"
            } else {
                button.textContent = "Error"
            }

        })
        .catch(err => {
            console.error(err);
            window.location.reload();
        })
        .finally(() => {
            LOADER.style.display = "none";
        })
    });
});

document.querySelectorAll(".watchall-btn").forEach(button => {
    button.addEventListener("click", () => {
        const confirmed = confirm("Are you sure to watch/unwatch the entire playlist?");
        if (!confirmed) return;

        const playlistId = button.dataset.playlist

        LOADER.style.display = "flex";
        button.textContent = "Please wait..."

        fetch(`/playlist/${playlistId}/watch_all`, {method: "POST"})
        .then(response => response.json())
        .then(data => {
            if (data.status === "watched") {
                document.querySelectorAll(".watch-btn").forEach(button => {
                    button.classList.add("watched")
                    button.textContent = "Watched";
                })
                button.textContent = "Unwatch all"
                button.classList.add("watched")
            } else if (data.status === "unwatched") {
                document.querySelectorAll(".watch-btn").forEach(button => {
                    button.classList.remove("watched")
                    button.textContent = "Not watched";
                })
                button.textContent = "Watch all"
                button.classList.remove("watched")
            } else if (data.status === "not saved") {
                button.textContent = "Save the playlist first!"
            } else {
                button.textContent = "Error"
            }
        })
        .catch(err => {
            console.error(err);
            window.location.reload();
        })
        .finally(() => {
            LOADER.style.display = "none";
        })
    })
});

document.querySelectorAll(".fetch-btn").forEach(button => {
    button.addEventListener("click", () => {
        const playlistId = button.dataset.playlist

        LOADER.style.display = "flex";
        button.disabled = true;
        button.textContent = "Refreshing..."

        fetch(`/fetch_playlist/${playlistId}`, {method: "POST"})
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                button.textContent = "Refreshed!"
                button.disabled = false
            }
        })
        .catch(err => {
            console.error(err);
            window.location.reload();
        })
        .finally(() => {
            LOADER.style.display = "none";
        })
    })
});

document.querySelectorAll(".fetchall-btn").forEach(button => {
    button.addEventListener("click", async () => {
        const playlists = button.dataset.playlists.split(",").filter(id => id)
        const total = playlists.length
        if (total < 1) return

        LOADER.style.display = "flex";
        button.disabled = true
        button.textContent = "Refreshing..."

        let current = 1
        for (const id of playlists) {
            try {
                button.textContent = `Refreshing... (${current}/${total})`
                const response = await fetch(`/fetch_playlist/${id}`, { method: "POST" })
                const data = await response.json()
                if (data.status === "success") {
                    current += 1
                }
                else {
                    console.log(data);
                }
            }
            catch (err) {
                console.error(err);
                window.location.reload();
            }
        }

        button.textContent = "Refreshed!"
        button.disabled = false
        LOADER.style.display = "none";
    })
});

document.querySelectorAll(".playlist-details-btn").forEach(button => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        POPUP.style.display = "flex";

        document.getElementById("closePopup").onclick = () => {
            POPUP.style.display = "none";
        }
    })
})

document.querySelectorAll(".preference-form select").forEach(select => {
    select.addEventListener("change", () => {
        const form = select.closest("form");

        LOADER.style.display = "flex";
        const body = new FormData(form)
        select.disabled = true;

        fetch("/set_preference", { method: "POST", body: body })
        .then(response => response.json())
        .then(data => {
            select.disabled = false;
            if (data.status === "success") {
                window.location.reload()
            }
            else if (data.status === "error") {
                console.error("Something went wrong.")
            }
        })
        .catch(err => {
            console.error(err);
            window.location.reload();
        })
        .finally(() => {
            LOADER.style.display = "none";
        })
    })
})

document.querySelectorAll(".preference-toggle input[type='checkbox']").forEach(checkbox => {
    checkbox.addEventListener("change", () => {
        const body = new FormData();
        body.append(checkbox.name, checkbox.checked ? "1" : "0");

        LOADER.style.display = "flex";
        checkbox.disabled = true;

        fetch("/set_preference", { method: "POST", body: body })
        .then(response => response.json())
        .then(data => {
            checkbox.disabled = false;
            if (data.status === "success") {
                window.location.reload()
            }
            else if (data.status === "error") {
                console.error("Something went wrong.")
            }
        })
        .catch(err => {
            console.error(err);
            window.location.reload();
        })
        .finally(() => {
            LOADER.style.display = "none";
        })
    })
})

document.querySelectorAll(".del-acc-btn").forEach(button => {
    button.addEventListener("click", () => {
        const confirmed = confirm("All your data will be permanently deleted. Are you sure?");
        if (!confirmed) return;

        document.getElementById("delete-account-button").style.display = "none"
        document.getElementById("delete-modal").style.display = "block";

        window.location.href = "/profile#delete-modal";

        document.getElementById("confirm-delete").onclick = () => {
            const password = document.getElementById("delete-password").value;
            if (!password) {
                LOADER.style.display = "none";
                return;
            }

            fetch("/delete_account", {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    password: password
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    alert("Your account has been deleted.");
                    window.location.href = "/login";
                } else if (data.status === "wrong_password") {
                    alert("Incorrect password.")
                    window.location.reload()
                } else {
                    alert("Something went wrong.")
                    window.location.reload()
                }
            })
        }
    })
})

/// SHOW LOADER WHEN SUBMITTING HTML FORMS AND CLICKING BUTTONS
document.addEventListener("DOMContentLoaded", () => {
    const forms = document.querySelectorAll(
        "#loginForm, #registerForm, #searchForm, #profileForm, #changePasswordForm"
    )

    const buttons = document.querySelectorAll(
        "#confirm-delete"
    )

    forms.forEach(form => {
        form.addEventListener("submit", () => {
            LOADER.style.display = "flex";
        });
    });

    buttons.forEach(button => {
        button.addEventListener("click", () => {
            LOADER.style.display = "flex";
        });
    });
});

/// HIDE LOADER WHEN USING BACK BUTTON
window.addEventListener("pageshow", event => {
    if (event.persisted) {
        LOADER.style.display = "none";
    }
});

/// FOR APPLE IOS SAFARI STANDALONE APP
document.querySelectorAll("a").forEach(a => {
    a.addEventListener("click", e => {
        LOADER.style.display = "flex";
        if (window.navigator.standalone && a.hostname === location.hostname) {
            e.preventDefault();
            window.location.href = a.href;
        }
    });
});