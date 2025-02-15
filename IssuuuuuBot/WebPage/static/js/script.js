// Função para confirmar a exclusão do áudio
function confirmDelete() {
    return confirm("Você tem certeza que deseja deletar este áudio?");
}

window.onload = function() {
        // Pegue as mensagens de flash
        const messages = document.querySelectorAll('.message');
        
        // Verifique se há mensagens e desapareça após 5 segundos
        messages.forEach(message => {
            setTimeout(() => {
                message.style.opacity = 0;
            }, 3000); // 5 segundos
        });
    };