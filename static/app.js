const LOADER = document.getElementById("loader-wrapper")
const POPUP = document.getElementById("popup")

function handleUnauthorized() {
    alert("User not logged in or session expired.");
    window.location.replace("/login");
}

function handleInternalServerError() {
    alert("Internal server error occurred.");
}

document.querySelectorAll(".save-btn").forEach(button => {
    button.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();

        const channelId = button.dataset.channel_id;
        const playlistId = button.dataset.playlist_id;

        LOADER.style.display = "flex";
        button.textContent = "Saving...";

        try {
            /// Check if the channel exists
            let channel_exists = false;
            let response = await fetch(`/api/channels/${channelId}`);
            if (response.status === 401)
                return handleUnauthorized();
            channel_exists = response.ok;

            /// If channel does not exist, try to save it
            if (!channel_exists) {
                response = await fetch("/api/channels", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({channel_id: channelId})
                });

                if (!response.ok) {
                    if (response.status === 401)
                        return handleUnauthorized();
                    if (response.status === 409)
                        console.log("Channel already exists.");
                    if (response.status === 500)
                        return handleInternalServerError();
                }
            }

            /// Try to save the playlist
            response = await fetch("/api/playlists", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({channel_id: channelId, playlist_id: playlistId})
            });

            if (!response.ok) {
                if (response.status === 401)
                    return handleUnauthorized();
                if (response.status === 409) {
                    alert("This playlist is already saved.")
                    button.textContent = "Already saved!";
                    button.disabled = true;
                    return;
                }
                if (response.status === 500)
                    return handleInternalServerError();
            }

            /// Try to save the playlist's videos
            response = await fetch("/api/videos", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({playlist_id: playlistId})
            });

            if (!response.ok) {
                if (response.status === 401)
                    return handleUnauthorized();
                if (response.status === 500)
                    return handleInternalServerError();
            }

            button.textContent = "Saved!";
            button.disabled = true;
        }
        catch (error) {
            console.error("An error occurred: ", error);
            button.textContent = "Error";
        }
        finally {
            LOADER.style.display = "none";
        }
    });
});

document.querySelectorAll(".delete-btn").forEach(button => {
    button.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();

        const confirmed = confirm("Are you sure to delete this playlist?");
        if (!confirmed) return;

        const playlistId = button.dataset.playlist_id;

        LOADER.style.display = "flex";
        button.textContent = "Deleting...";

        try {
            const response = await fetch(`/api/playlists/${playlistId}`, { method: "DELETE" });

            if (!response.ok) {
                if (response.status === 401)
                    return handleUnauthorized();
                if (response.status === 404) {
                    alert("This playlist was not found.");
                    button.textContent = "Already deleted!";
                    button.disabled = true;
                    return;
                }
                if (response.status === 500)
                    return handleInternalServerError();
            }

            button.textContent = "Deleted!";
            button.disabled = true;
        }
        catch (error) {
            console.error("An error occurred: ", error);
            button.textContent = "Error";
        }
        finally {
            LOADER.style.display = "none";
        }
    });
});

document.querySelectorAll(".watch-btn").forEach(button => {
    button.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();

        const videoId = button.dataset.video_id;

        LOADER.style.display = "flex";
        button.textContent = "Please wait...";

        try {
            const is_watched = button.classList.contains("watched");

            const response = await fetch(`/api/videos/${videoId}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ watched: !is_watched })
            })

            if (!response.ok) {
                if (response.status === 401)
                    return handleUnauthorized();
                if (response.status === 404) {
                    alert("Please save the playlist first!");
                    button.textContent = "Not watched";
                    return;
                }
                if (response.status === 500)
                    return handleInternalServerError();
            }

            const data = await response.json();

            if (data.watched) {
                button.textContent = "Watched";
                button.classList.add("watched");
            }
            else {
                button.textContent = "Not watched";
                button.classList.remove("watched");
            }
        }
        catch (error) {
            console.error("An error occurred: ", error);
            button.textContent = "Error";
        }
        finally {
            LOADER.style.display = "none";
        }
    });
});

document.querySelector(".watchall-btn")?.addEventListener("click", async (event) => {
    event.preventDefault();
    event.stopPropagation();

    const confirmed = confirm("Are you sure to watch/unwatch the entire playlist?");
    if (!confirmed) return;

    const button = event.currentTarget;
    const playlistId = button.dataset.playlist_id

    LOADER.style.display = "flex";
    button.textContent = "Please wait..."

    try {
        const is_watched = button.classList.contains("watched");

        const response = await fetch(`/api/videos`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                playlist_id: playlistId,
                watched: !is_watched
            })
        });

        if (!response.ok) {
            if (response.status === 401)
                return handleUnauthorized();
            if (response.status === 404) {
                alert("Please save the playlist first!");
                button.textContent = "Watch all";
                return;
            }
            if (response.status === 500)
                return handleInternalServerError();
        }

        const data = await response.json();

        /// Update the 'watch all' button and all the 'watch' buttons
        if (data.watched) {
            button.classList.add("watched");
            button.textContent = "Unwatch all";
            document.querySelectorAll(".watch-btn").forEach(b => {
                b.classList.add("watched");
                b.textContent = "Watched";
            });
        }
        else {
            button.classList.remove("watched");
            button.textContent = "Watch all";
            document.querySelectorAll(".watch-btn").forEach(b => {
                b.classList.remove("watched");
                b.textContent = "Not watched";
            });
        }
    }
    catch (error) {
        console.error("An error occurred: ", error);
        button.textContent = "Error";
    }
    finally {
        LOADER.style.display = "none";
    }
});

document.querySelector(".refresh-btn")?.addEventListener("click", async (event) => {
    event.preventDefault();
    event.stopPropagation();

    const button = event.currentTarget;
    const playlistId = button.dataset.playlist_id;

    LOADER.style.display = "flex";
    button.disabled = true;
    button.textContent = "Refreshing...";

    try {
        let response = await fetch(`/api/playlists/${playlistId}`, { method: "PUT" });

        if (!response.ok) {
            if (response.status === 401)
                return handleUnauthorized();
            if (response.status === 404) {
                alert("This playlist is not saved.")
                button.textContent = "Refresh";
                return;
            }
            if (response.status === 500)
                return handleInternalServerError();
        }

        response = await fetch("/api/videos", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ playlist_id: playlistId })
        });

        if (!response.ok) {
            if (response.status === 401)
                return handleUnauthorized();
            if (response.status === 500)
                return handleInternalServerError();
        }

        button.textContent = "Refreshed!";
    }
    catch (error) {
        console.error("An error occurred: ", error);
        button.textContent = "Error";
    }
    finally {
        LOADER.style.display = "none";
        button.disabled = false;
    }
});

///// vvv TO-DO vvv /////

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

        // POPUP.style.display = "flex";
        POPUP.classList.add("visible");

        document.getElementById("closePopup").onclick = () => {
            POPUP.classList.remove("visible");
            // POPUP.style.display = "none";
        }
    })
})

document.querySelectorAll(".youtube-btn").forEach(button => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        const type = button.dataset.type;
        const id = button.dataset.id;

        const confirmed = confirm(`Open this ${type} on YouTube?`);
        if (!confirmed) return;

        let url = "";
        if (type === "playlist") {
            url = `https://youtube.com/playlist?list=${id}`;
        }
        else if (type === "channel") {
            url = `https://youtube.com/channel/${id}`;
        }

        if (url) {
            // noinspection SpellCheckingInspection
            window.open(url, "_blank", "noopener, noreferrer");
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
        // noinspection JSUnresolvedReference
        if (window.navigator.standalone && a.hostname === location.hostname) {
            e.preventDefault();
            window.location.href = a.href;
        }
    });
});