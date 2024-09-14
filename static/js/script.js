document.addEventListener('DOMContentLoaded', (event) => {
    const socket = io();
    const mensajesDiv = document.getElementById('mensajes');
    const formularioMensaje = document.getElementById('formulario-mensaje');
    const mensajeInput = document.getElementById('mensaje');
    const listaUsuarios = document.getElementById('lista-usuarios');

    function cargarMensajes() {
        fetch('/obtener_mensajes')
            .then(response => response.json())
            .then(mensajes => {
                actualizarMensajes(mensajes);
            })
            .catch(error => console.error('Error:', error));
    }

    function actualizarMensajes(mensajes) {
        mensajesDiv.innerHTML = '';
        mensajes.forEach(mensaje => {
            const mensajeElement = document.createElement('div');
            mensajeElement.className = 'mb-2';
            mensajeElement.innerHTML = `<strong>${mensaje.nombre}:</strong> ${mensaje.mensaje}`;
            mensajesDiv.appendChild(mensajeElement);
        });
        mensajesDiv.scrollTop = mensajesDiv.scrollHeight;
    }

    socket.on('connect', () => {
        console.log('Conectado al servidor');
        socket.emit('solicitar_usuarios_conectados');
        cargarMensajes();
    });

    socket.on('usuarios_conectados', (usuarios) => {
        listaUsuarios.innerHTML = '';
        usuarios.forEach(usuario => {
            const li = document.createElement('li');
            li.innerHTML = `<a href="/perfil/${usuario.id}" class="text-pastel-300 hover:text-pastel-400 transition duration-300">${usuario.nombre}</a>`;
            listaUsuarios.appendChild(li);
        });
    });

    socket.on('nuevo_mensaje', (mensajes) => {
        actualizarMensajes(mensajes);
    });

    formularioMensaje.addEventListener('submit', (e) => {
        e.preventDefault();
        if (mensajeInput.value.trim()) {
            socket.emit('enviar_mensaje', { mensaje: mensajeInput.value });
            mensajeInput.value = '';
        }
    });

    // Cargar mensajes al iniciar la página
    cargarMensajes();
});
