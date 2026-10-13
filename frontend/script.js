let socket = null;

let currentUsername = "";
let currentRoom = "general";

let chatMode = "room";
let privateTarget = "";

const WS_URL = "ws://127.0.0.1:8765";

const loginSection = document.getElementById("login-section");
const chatSection = document.getElementById("chat-section");

const usernameInput = document.getElementById("username");
const joinButton = document.getElementById("join-btn");
const loginStatus = document.getElementById("login-status");

const currentUser = document.getElementById("current-user");
const chatTitle = document.getElementById("chat-title");
const chatSubtitle = document.getElementById("chat-subtitle");
const connectionState = document.getElementById("connection-state");

const messages = document.getElementById("messages");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-btn");

const usersButton = document.getElementById("users-btn");
const roomsButton = document.getElementById("rooms-btn");
const roomChatButton = document.getElementById("room-chat-btn");
const privateButton = document.getElementById("private-btn");
const helpButton = document.getElementById("help-btn");

const modal = document.getElementById("modal");
const modalTitle = document.getElementById("modal-title");
const modalContent = document.getElementById("modal-content");
const modalClose = document.getElementById("modal-close");


// STATUS

function setStatus(text) {
    loginStatus.textContent = text;
}


// ADD MESSAGE TO CHAT


function addMessage(text, type = "normal") {

    const item = document.createElement("div");

    item.className = `message ${type}`;

    item.textContent = text;

    messages.appendChild(item);

    messages.scrollTop = messages.scrollHeight;
}


// ============================================================
// CLEAR CHAT
// ============================================================

function clearMessages() {

    messages.innerHTML = "";
}


// ============================================================
// SHOW CHAT APPLICATION
// ============================================================

function showChat() {

    loginSection.classList.add("hidden");

    chatSection.classList.remove("hidden");

    currentUser.textContent = currentUsername;

    setRoomChat();

    messageInput.disabled = false;

    sendButton.disabled = false;

    messageInput.focus();
}


// ============================================================
// CONNECT WEBSOCKET
// ============================================================

function connectWebSocket() {

    return new Promise((resolve, reject) => {

        socket = new WebSocket(WS_URL);


        socket.onopen = () => {

            connectionState.textContent = "● Online";

            connectionState.className = "online";

            resolve();
        };


        socket.onerror = (error) => {

            console.error("WebSocket error:", error);

            reject(error);
        };


        socket.onclose = () => {

            connectionState.textContent = "● Disconnected";

            connectionState.className = "offline";
        };


        socket.onmessage = (event) => {

            handleServerMessage(event.data);
        };

    });
}


// ============================================================
// JOIN CHAT
// ============================================================

async function joinChat() {

    const username = usernameInput.value.trim();


    if (!username) {

        setStatus("Please enter a username.");

        return;
    }


    joinButton.disabled = true;

    setStatus("Connecting...");


    try {

        if (
            !socket ||
            socket.readyState !== WebSocket.OPEN
        ) {

            await connectWebSocket();
        }


        socket.send(
            JSON.stringify({
                type: "join",
                username: username
            })
        );


    } catch (error) {

        console.error(error);

        setStatus(
            "Could not connect to chat server."
        );

        joinButton.disabled = false;
    }
}


// ============================================================
// HANDLE SERVER MESSAGE
// ============================================================

function handleServerMessage(data) {

    let response = null;


    // --------------------------------------------------------
    // Try JSON first
    // --------------------------------------------------------

    try {

        response = JSON.parse(data);

    } catch (_) {

        response = null;
    }


    // --------------------------------------------------------
    // JOIN SUCCESS
    // --------------------------------------------------------

    if (
        response &&
        response.type === "join_success"
    ) {

        currentUsername = response.username;

        currentRoom =
            response.room || "general";

        setStatus("");

        showChat();

        /*
         * IMPORTANT:
         * Do NOT display the old TCP server welcome message.
         *
         * The web application now starts directly in General.
         */

        return;
    }


    // --------------------------------------------------------
    // JOIN ERROR
    // --------------------------------------------------------

    if (
        response &&
        response.type === "join_error"
    ) {

        setStatus(
            response.message ||
            "Unable to join."
        );

        joinButton.disabled = false;

        return;
    }


    // --------------------------------------------------------
    // ONLINE USERS
    // --------------------------------------------------------

    if (
        response &&
        response.type === "users"
    ) {

        showUsers(
            response.users || []
        );

        return;
    }


    // --------------------------------------------------------
    // NORMAL TCP SERVER MESSAGE
    // --------------------------------------------------------

    const text = String(data).trim();


    if (!text) {

        return;
    }


    /*
     * The TCP server still sends its old
     * command/help text when a client joins.
     *
     * We keep that on the server because the
     * TCP application uses it, but DO NOT show
     * it in the browser.
     */

    const hiddenServerText = [
        "You are in room:",
        "Commands:",
        "/help",
        "/rooms",
        "/users",
        "/join <room>",
        "/msg <username>",
        "/quit",
        "Welcome"
    ];


    const isOldWelcomeMessage =
        hiddenServerText.some(
            phrase => text.includes(phrase)
        );


    if (isOldWelcomeMessage) {

        return;
    }


    // --------------------------------------------------------
    // DISPLAY NORMAL MESSAGE
    // --------------------------------------------------------

    addMessage(
        text,
        "normal"
    );
}


// ============================================================
// SEND CHAT MESSAGE
// ============================================================

function sendChatMessage() {

    const message =
        messageInput.value.trim();


    if (!message) {

        return;
    }


    if (
        !socket ||
        socket.readyState !== WebSocket.OPEN
    ) {

        addMessage(
            "SYSTEM: Not connected.",
            "system"
        );

        return;
    }


    // --------------------------------------------------------
    // PRIVATE MESSAGE
    // --------------------------------------------------------

    if (
        chatMode === "private" &&
        privateTarget
    ) {

        socket.send(
            `/msg ${privateTarget} ${message}`
        );


        addMessage(
            `You → ${privateTarget}: ${message}`,
            "self"
        );

    }

    // --------------------------------------------------------
    // ROOM MESSAGE
    // --------------------------------------------------------

    else {

        socket.send(message);


        addMessage(
            `You: ${message}`,
            "self"
        );
    }


    messageInput.value = "";

    messageInput.focus();
}


// ============================================================
// ROOM CHAT
// ============================================================

function setRoomChat() {

    chatMode = "room";

    privateTarget = "";


    const roomName =
        currentRoom.charAt(0).toUpperCase() +
        currentRoom.slice(1);


    chatTitle.textContent =
        roomName;


    chatSubtitle.textContent =
        "Room Chat";


    messageInput.placeholder =
        "Type a message to the room...";


    messageInput.focus();
}


// ============================================================
// PRIVATE CHAT
// ============================================================

function setPrivateChat(username) {

    chatMode = "private";

    privateTarget = username;


    chatTitle.textContent =
        `Private Message → ${username}`;


    chatSubtitle.textContent =
        "Private Chat";


    messageInput.placeholder =
        `Message ${username} privately...`;


    closeModal();

    messageInput.focus();
}


// ============================================================
// MODAL
// ============================================================

function openModal(title, content) {

    modalTitle.textContent = title;

    modalContent.innerHTML = "";

    modalContent.appendChild(content);

    modal.classList.remove("hidden");
}


// ============================================================
// CLOSE MODAL
// ============================================================

function closeModal() {

    modal.classList.add("hidden");

    modalContent.innerHTML = "";
}


// ============================================================
// CREATE MODAL BUTTON
// ============================================================

function createButton(
    text,
    callback
) {

    const button =
        document.createElement("button");


    button.className =
        "modal-option";


    button.textContent =
        text;


    button.addEventListener(
        "click",
        callback
    );


    return button;
}


// ============================================================
// SHOW ONLINE USERS
// ============================================================

function showUsers(users) {

    const box =
        document.createElement("div");


    box.className =
        "option-list";


    // Remove current user from list
    const otherUsers =
        users.filter(
            user =>
                user.toLowerCase() !==
                currentUsername.toLowerCase()
        );


    if (otherUsers.length === 0) {

        const empty =
            document.createElement("p");


        empty.className =
            "empty";


        empty.textContent =
            "No other users are online.";


        box.appendChild(empty);

    } else {

        otherUsers.forEach(
            user => {

                const button =
                    createButton(
                        `🟢 ${user}`,
                        () =>
                            setPrivateChat(user)
                    );


                box.appendChild(button);
            }
        );
    }


    openModal(
        "Online Users",
        box
    );
}


// ============================================================
// REQUEST ONLINE USERS
// ============================================================

function requestUsers() {

    if (
        !socket ||
        socket.readyState !== WebSocket.OPEN
    ) {

        return;
    }


    socket.send(
        "__GET_USERS__"
    );
}


// ============================================================
// SHOW CHAT ROOMS
// ============================================================

function showRooms() {

    const box =
        document.createElement("div");


    box.className =
        "option-list";


    const rooms = [
        "general",
        "project",
        "gaming"
    ];


    rooms.forEach(
        room => {

            const displayName =
                room.charAt(0).toUpperCase() +
                room.slice(1);


            const button =
                createButton(
                    `🏠 ${displayName}`,
                    () => {

                        currentRoom =
                            room;


                        socket.send(
                            `/join ${room}`
                        );


                        setRoomChat();

                        closeModal();


                        addMessage(
                            `SYSTEM: Joined ${displayName} room.`,
                            "system"
                        );
                    }
                );


            box.appendChild(button);
        }
    );


    // --------------------------------------------------------
    // CUSTOM ROOM
    // --------------------------------------------------------

    const custom =
        document.createElement("div");


    custom.className =
        "custom-room";


    const input =
        document.createElement("input");


    input.placeholder =
        "Enter another room name";


    const button =
        document.createElement("button");


    button.textContent =
        "JOIN";


    button.addEventListener(
        "click",
        () => {

            const room =
                input.value.trim();


            if (!room) {

                return;
            }


            currentRoom =
                room;


            socket.send(
                `/join ${room}`
            );


            setRoomChat();

            closeModal();


            addMessage(
                `SYSTEM: Joined ${room} room.`,
                "system"
            );
        }
    );


    custom.appendChild(input);

    custom.appendChild(button);

    box.appendChild(custom);


    openModal(
        "Chat Rooms",
        box
    );
}


// ============================================================
// HELP
// ============================================================

function showHelp() {

    const box =
        document.createElement("div");


    box.className =
        "help-content";


    box.innerHTML = `
        <p>
            <strong>👥 Online Users</strong><br>
            View everyone currently connected.
        </p>

        <p>
            <strong>🏠 Chat Rooms</strong><br>
            View and join available chat rooms.
        </p>

        <p>
            <strong>💬 Room Chat</strong><br>
            Chat with everyone in your current room.
        </p>

        <p>
            <strong>🔒 Private Message</strong><br>
            Select an online user and send a
            private message only to that user.
        </p>

        <p>
            <strong>❓ Help</strong><br>
            Show these instructions.
        </p>

        <p>
            <strong>Current Room</strong><br>
            ${currentRoom}
        </p>
    `;


    openModal(
        "Help",
        box
    );
}


// ============================================================
// BUTTON EVENTS
// ============================================================

joinButton.addEventListener(
    "click",
    joinChat
);


usernameInput.addEventListener(
    "keydown",
    event => {

        if (event.key === "Enter") {

            joinChat();
        }
    }
);


sendButton.addEventListener(
    "click",
    sendChatMessage
);


messageInput.addEventListener(
    "keydown",
    event => {

        if (event.key === "Enter") {

            event.preventDefault();

            sendChatMessage();
        }
    }
);


// Online Users
usersButton.addEventListener(
    "click",
    requestUsers
);


// Chat Rooms
roomsButton.addEventListener(
    "click",
    showRooms
);


// Room Chat
roomChatButton.addEventListener(
    "click",
    () => {

        setRoomChat();

        addMessage(
            `SYSTEM: Current room is ${currentRoom}.`,
            "system"
        );
    }
);


// Private Message
privateButton.addEventListener(
    "click",
    requestUsers
);


// Help
helpButton.addEventListener(
    "click",
    showHelp
);


// Close modal
modalClose.addEventListener(
    "click",
    closeModal
);


// Click outside modal
modal.addEventListener(
    "click",
    event => {

        if (event.target === modal) {

            closeModal();
        }
    }
);


// ============================================================
// INITIAL STATE
// ============================================================

messageInput.disabled = true;

sendButton.disabled = true;
