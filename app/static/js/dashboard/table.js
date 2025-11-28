async function carregarDados() {
    const response = await fetch('/api/comparar-quantidade');
    const data = await response.json();

    // Inicializa ou atualiza o DataTable
    if (!$.fn.DataTable.isDataTable('#tabela-pecas')) {
        const table = $('#tabela-pecas').DataTable({
            data: data,
            columns: [
                { data: 'almoxarifado' },
                { data: 'local' },
                { data: 'codigo' },
                { data: 'descricao' },
                {
                    data: 'peca_fora_lista',
                    render: function (data) {
                        return data === false ? 'Não' : 'Sim';
                    }
                },
                {
                    data: 'quantidade_sistema',
                    render: function (data) {
                        return data !== null ? data : 'Não registrada';
                    }
                },
                {
                    data: 'quantidade_real',
                    render: function (data) {
                        const value = data !== null ? data : '';
                        return `<input type="number" class="form-control form-control-sm input-quantidade-real" value="${value}" step=".01" min="0">`;
                    }
                },
                {
                    data: 'diferenca',
                    render: function (data) {
                        return data !== null ? data : 'N/A';
                    }
                },
                {
                    data: null,
                    orderable: false,
                    searchable: false,
                    render: function () {
                        return '<button class="btn btn-primary btn-sm btn-salvar-quantidade">Salvar</button>';
                    }
                }
            ],
            language: {
                url: "https://cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json"
            },
            pageLength: 10,
            lengthChange: false,
            order: [[6, 'desc']]
        });

        // Filtro personalizado para Almoxarifado
        $('#filtro-almoxarifado').on('keyup', function () {
            table.column(0).search(this.value).draw();
        });

        // Evento para salvar a quantidade real de uma linha
        $('#tabela-pecas tbody').on('click', '.btn-salvar-quantidade', async function () {
            const tableInstance = $('#tabela-pecas').DataTable();
            const $row = $(this).closest('tr');
            const rowData = tableInstance.row($row).data();
            const input = $row.find('.input-quantidade-real');
            const novaQuantidade = input.val();

            if (!novaQuantidade && novaQuantidade !== '0') {
                Swal.fire({
                    title: 'Informe a quantidade real',
                    icon: 'warning'
                });
                return;
            }

            try {
                const response = await fetch('/api/quantidade-real', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        peca_id: rowData.peca_id,
                        quantidade_real: novaQuantidade
                    })
                });

                const json = await response.json();

                if (response.ok) {
                    Swal.fire({
                        title: json.message,
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false
                    });

                    const quantidadeSistema = rowData.quantidade_sistema;
                    const quantidadeRealNumber = parseFloat(novaQuantidade);

                    rowData.quantidade_real = quantidadeRealNumber;
                    if (quantidadeSistema !== null && quantidadeSistema !== undefined) {
                        rowData.diferenca = quantidadeRealNumber - quantidadeSistema;
                    } else {
                        rowData.diferenca = null;
                    }

                    tableInstance.row($row).data(rowData).invalidate();
                } else {
                    Swal.fire({
                        title: json.message || 'Erro ao salvar quantidade',
                        icon: 'error'
                    });
                }
            } catch (error) {
                console.error('Erro ao atualizar quantidade real:', error);
                Swal.fire({
                    title: 'Erro de comunicação com o servidor',
                    icon: 'error'
                });
            }
        });
    } else {
        const table = $('#tabela-pecas').DataTable();
        table.clear();
        table.rows.add(data);
        table.draw();
    }
}

carregarDados();
