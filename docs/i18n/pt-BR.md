# Clean Your TV — guia de uso

No-root e Root são opções equivalentes para diferentes configurações da TV. Escolha No-root para LG Developer Mode ou Root se já tiver acesso root por SSH. A compatibilidade e os testes realizados são específicos de cada edição.

## Requisitos

Este guia descreve **[v1.2.0 estável](https://github.com/Razdva122/clean-your-tv-lg-webos/releases/tag/v1.2.0)**. Os links `releases/latest/download` entregam a versão estável publicada. Veja [instalação](../INSTALL.md) e [notas da versão](../RELEASE-1.2.0.md).

Versões da publicação: cytv **0.3.1**, Home **1.4.1**, Home Helper **0.6.19**, Root **0.3.0**, Home Updater e Root Updater **0.2.1**, Android **0.2.1-preview** (código **10**), supervisor System Updater **1.0.0**, protocolo **1**.

Ligue a TV e conecte os dois dispositivos à mesma rede local confiável. Depois, o computador pode ficar desligado. A compatibilidade depende do modelo, firmware e controle remoto; Root ainda tem testes em hardware pendentes.

- **No-root:** ative LG Developer Mode e Key Server. Digite a frase de acesso exibida na TV e aceite nela o pedido separado de pareamento. Developer Mode deve continuar ativo: a expiração pode remover aplicativos instalados por esse método. Confira o cronômetro oficial mesmo com a renovação Beta ativada. O monitoramento do Helper depende da rede local.

O Helper No-root atualizado exige Node.js 0.12.2 ou posterior na TV. O instalador verifica esse requisito antes da instalação. Pacotes publicados anteriormente não recebem essa compatibilidade automaticamente; o acesso ao controle, a espera e a inicialização a frio precisam ser testados em cada modelo.

- **Root:** é necessário acesso SSH root já existente. O instalador não faz root. Não ative Developer Mode em uma TV que já tenha root. Mantenha o acesso root e os serviços de recuperação disponíveis.

## Python opcional para Root

Root exige Python 3.9+ na TV. O instalador verifica os módulos e operações de verdade, incluindo `json`, `fcntl`, bloqueios, arquivos e subprocessos; o número da versão não basta. Se o interpretador existente for adequado, não há outro download de Python. Caso contrário, durante a configuração, o computador ou Android pode baixar CPython **3.13.17 para ARMv7 soft-float**, fixado por URL, tamanho e SHA-256, e transferi-lo pela conexão SSH já confiável. Os pacotes comuns dos instaladores não incluem esse arquivo; a TV não precisa de Internet nessa etapa.

O download opcional tem cerca de **26,3 MB**, a transferência SSH normalizada **51,5 MB** e os arquivos instalados **119,3 MB**; a preparação exige **320 MiB** livres na TV. A compatibilidade do carregador e das bibliotecas é verificada antes da ativação. O runtime ocupa versões privadas em `/var/lib/clean-your-tv-python/`, sem alterar Python do sistema, libc ou PATH global. Os demais requisitos continuam: root, serviços webOS adequados e Node.js **8+** para Root/System Updater; o Helper No-root precisa de Node.js **0.12.2+**.

Em um computador com Internet, prepare o cache verificado sem descobrir nem contatar uma TV:

```sh
./cytv --prepare-python-runtime --data-dir /caminho/cache-privado
```

Use o mesmo `--data-dir` na instalação. Para transportar o cache, crie uma pasta privada separada, sem suas chaves SSH e perfis habituais. `status`, `doctor`, `restore` e `uninstall` não baixam Python automaticamente. Preserve as versões usadas por Root, atualizadores e recuperação, mesmo depois de remover os aplicativos. Detalhes: [runtime opcional](../OPTIONAL-PYTHON.md).

## Instalação e idioma

- **Windows x64:** baixe `cytv-windows-x64-desktop.zip`, escolha **Extrair tudo** no Explorador de Arquivos e abra `cytv-desktop/cytv-desktop.exe`. Mantenha a pasta `_internal` ao lado. A assinatura de editor do Windows não está configurada. O console separado é `cytv-windows-x64.exe`; renomeie para `cytv.exe` e use `.\cytv.exe` no PowerShell para os comandos abaixo.
- **macOS 13+:** extraia `cytv-macos-arm64.zip` para Apple Silicon ou `cytv-macos-x64.zip` para Intel; mova `cytv.app` para Aplicativos e abra. Permita acesso à rede local. Se uma cópia confiável for bloqueada, use Privacidade e Segurança → Abrir Mesmo Assim; não desative o Gatekeeper. A compatibilidade com sistemas antigos não foi confirmada.
- **Linux x64:** no Ubuntu 22.04+, Debian 12+ ou Mint 21+, instale `cytv-linux-x64.deb` com o gerenciador gráfico de pacotes e abra Clean Your TV pelo menu. Pode ser necessário acesso à Internet para bibliotecas. Não há pacote Linux ARM. O executável independente `cytv-linux-x64` é a CLI; use o `.deb` para o app gráfico.

[Instalador Android](../../android/README.md): inclui os dez idiomas da interface. O controle no canto superior direito mostra o idioma atual; toque para escolher outro. A seleção fica salva no telefone.

No Android, a ação de manutenção escolhida continua visível durante a conexão e mostra seu próprio progresso. A interface usa a fonte do sistema do telefone, com rótulos e textos de ajuda maiores.

O assistente usa inicialmente o idioma do sistema e salva sua escolha explícita. Na TV, abra **Configurações → Idioma** e escolha um idioma ou a opção automática do sistema. As preferências da TV e do instalador são independentes. Veja os códigos no [índice de idiomas](../LANGUAGES.md).

Para a CLI baixada separadamente no macOS/Linux, na pasta extraída:

```sh
chmod +x cytv
./cytv --language pt-BR install
```

Escolha a TV ou informe o IP, selecione a edição e confira o resumo. Confirme uma nova identidade SSH apenas para sua TV em uma rede confiável; uma chave salva que mudou bloqueia o acesso. Root prepara a recuperação e ativa Home imediatamente, sem período de teste nem etapa de confirmação para manter. Teste setas, OK, Home, Voltar/Cancelar, volume, espera e inicialização a frio.

Se a remoção de Root for interrompida, escolha Remover novamente no app. Ele verifica o registro da TV e os pacotes antes de continuar; não repete uma remoção concluída. Se ainda estiver em andamento, aguarde um minuto. Se o resultado não puder ser verificado, reinicie a TV e verifique novamente; guarde o relatório para o suporte.

## Uso e recuperação

Setas selecionam; OK abre; segure OK para reorganizar. Um toque em Voltar mantém a navegação e a confirmação de saída do aplicativo. Home abre o lançador com o controle ativo. Nas novas compilações, segure Voltar por 1,2 segundos para abrir LG Home uma vez. O interruptor de controle do Home e suas configurações não mudam.

**Novas compilações: pressione Home três vezes em dois segundos**, soltando entre os toques. Isso restaura LG Home e interrompe o controle sem apagar preferências. No No-root Helper até a versão 0.6.13, segure Home por cerca de dois segundos. Segurar Home não é o gesto de emergência do Root.

No-root: abra **Home Helper** na lista de aplicativos LG para retomar; abrir apenas Home não remove a parada. Root: ative **Alterar Home** nas configurações do Home para retomar. **Abrir LG Home** abre LG Home uma vez sem mudar o destino de Home. Para restaurar LG Home como destino permanente, desative **Alterar Home** ou execute `cytv restore`. Nunca execute os dois controladores juntos. Se a falha voltar, mantenha LG Home ativo.

```sh
./cytv --language pt-BR status
./cytv --language pt-BR doctor --report
./cytv --language pt-BR restore
./cytv --language pt-BR uninstall
```

Após uma interrupção, execute primeiro `status` e preserve os registros. `restore` restaura LG Home sem remover aplicativos; `uninstall` restaura antes de remover. Os dados de recuperação Root são mantidos de propósito: não os apague para forçar a reinstalação. Revise relatórios antes de compartilhar; não publique chaves nem pastas de perfis.

## Atualização e remoção

Após conectar, cytv mostra versão instalada → incluída e diferencia primeira instalação, reinstalação e retorno a uma versão anterior. Confira o resumo antes de confirmar; `--yes` mantém as verificações de compatibilidade. Guarde pacotes funcionais e cópias privadas das configurações. Ao atualizar pelo computador, pare o No-root Helper antes de substituir os pacotes; não desinstale primeiro. Não instale uma IPK isolada sobre Root ativo: use o procedimento adequado do cytv. Remover o aplicativo do computador não remove os aplicativos da TV.

A candidata acrescenta **Atualizar tudo** em Configurações → Atualizações de software. O System Updater independente verifica um conjunto assinado para a edição: Home, Helper e Home Updater para No-root em TV com root; Root Home, Root Updater e runtime de controle/recuperação para Root. Atualizar pela TV exige **root, Homebrew Channel**, Python adequado, Node.js 8+ e serviços webOS funcionais. Em TV sem root, use o computador.

Em uma instalação nova, use o instalador completo da candidata para preparar Home e o Updater de recuperação da edição. Essa versão de transição não está disponível no feed estável.

Se Root já estiver instalado e houver um Root Updater preservado, uma reinstalação genérica poderá ser recusada por segurança. Primeiro execute `status` e os diagnósticos, depois confira a transação e a recuperação no Updater existente. Resolva operações ativas ou incertas pelo fluxo de recuperação correspondente à instalação anterior; a transição de infraestrutura precisa ser avaliada conforme o estado real da TV. Não apague o diário nem contorne o bloqueio com `--yes`, uma IPK isolada ou OTA antigo. O OTA apenas do aplicativo não instala a nova infraestrutura. Siga o [verificação da TV existente](../UPDATES.md#one-time-computer-preparation).

Só depois de verificar uma configuração compatível com Home `systemUpdateProtocol = 1` e o Updater de recuperação adequado, habilite o supervisor pelo computador. No instalador, escolha habilitar as atualizações de todos os componentes da TV; para Root, com uma conexão SSH root salva:

```sh
./cytv --language pt-BR enable-system-updates --edition root --host TV_ADDRESS
```

Para No-root em TV com root, prepare Home/Helper/Home Updater pelo computador e siga o procedimento com alias SSH root em [Atualizações](../UPDATES.md#one-time-computer-preparation). O supervisor captura uma base verificada de recuperação dos componentes realmente instalados. O OTA antigo que troca apenas o aplicativo não instala o novo Python, supervisor ou infraestrutura dos atualizadores. Depois da preparação, use o fluxo comum; instaladores antigos conflitantes são recusados.

A instalação pede confirmação e depois verifica a inicialização automaticamente. Perfil e configurações são preservados; uma parada explícita ou de emergência do controle Home não é desfeita. Cima/Baixo percorre as notas, Esquerda/Direita escolhe as ações fixas e a atualização de estado mantém o foco do controle. Um ponto laranja indica nova versão, inclusive quando exige o computador. Abra Recuperação no Updater para consultar o estado e a versão anterior disponível. O retorno do sistema restaura todo o conjunto anterior e o perfil salvo; alterações posteriores nas configurações podem ser perdidas. A verificação automática de inicialização não apaga a recuperação, que permanece até a próxima transação.

Após uma interrupção, execute `status` e preserve o diário e os dados de recuperação. Um resultado incerto bloqueia reinstalação e retorno; ler a versão não comprova que o instalador terminou. Não apague diários, bloqueios ou versões do Python para forçar outra tentativa. `doctor --report` identifica cada requisito Root que falhou e registra códigos numéricos SSH sem credenciais ou saída bruta. Revise o relatório antes de compartilhar.

## Testes em hardware e limites

Root 0.2.0, Root Updater 0.2.0 e supervisor 1.0.0 foram verificados em OLED55C3RLA / firmware 43.21.71 / webOS 11.2.0 (`d344d92`, conteúdo idêntico a `4b66951`). Passaram controles, Home triplo e retomada, espera/retomada com Emby aberto por 70 segundos, menus de versões e aviso claro de feed indisponível. Inicialização a frio real, Helper 0.6.19 na TV, UK6540PTD e atualização/retorno completo assinado não foram testados. A publicação estável aceita essas evidências limitadas; outros modelos não estão validados.

No-root verifica a ABI do shell e aceita kernel de 64 bits somente com ambiente ARM32 confirmado. Nome de modelo ou `armv7l` não garante compatibilidade. As evidências anteriores continuam restritas ao hardware e aos pacotes testados.

No-root: Configurações Home → Modo de desenvolvedor reúne renovação Beta, verificação de sessão e diagnósticos. Confira sempre o cronômetro oficial. Home Helper mostra o estado e pede confirmação para retomar após uma parada.

Documentação técnica: [desktop](../DESKTOP_INSTALL.md), [CLI](../CLI.md), [instalação manual](../MANUAL_INSTALL.md), [recuperação](../RECOVERY.md), [edições](../EDITIONS.md), [atualizações](../UPDATES.md).

Se Root mostrar `Denied methods call status` logo após preparar o supervisor, feche e reabra Home Root uma vez e verifique as atualizações novamente. Se persistir, guarde o diagnóstico e o estado de recuperação.

1.2.0 (#51): após a TV rejeitar um pacote, o relatório JSON preserva apenas a categoria da operação, códigos numéricos limitados, um estado de pacote permitido e um resultado booleano. Exclui o texto bruto do erro da TV, caminhos e IDs de aplicativos. Revise antes de compartilhar; não há nova tentativa automática e a falha de instalação no UN70006LA ainda não foi confirmada como corrigida.

1.2.0 (#59): se o estado do Helper não puder ser verificado, **Iniciar Helper** continua disponível com confirmação. Abrir o bloco não reinicia o Helper nem cancela uma parada de emergência. Os ajustes de Home exigem que o controle responda.

1.2.0 (#55): o Root valida a migração antes de instalar. Uma instalação interrompida antes do provisionamento pode ser removida sem um snapshot LS2 que nunca foi criado; um registro verificado é preservado para o arquivamento e a reinstalação normais do cytv. Snapshots ausentes em etapas posteriores ou evidências conflitantes ainda bloqueiam a limpeza. Exige o novo driver; a falha ao iniciar o serviço de recuperação no OLED Flex continua sem solução.

## Bloqueio de firmware LG no 1.2.0

Somente Root: Configurações do Home → Atualizações de firmware da LG altera a configuração existente do Homebrew Channel. Inclui atualizações de segurança do firmware; as do Clean Your TV são separadas. Ambas as alterações exigem reiniciar a TV de verdade; o modo de espera não basta. O botão mostra a configuração salva, não um bloqueio ativo verificado. Algumas TVs verificam antes do bloqueio; os avisos podem continuar e pode ser necessário bloquear no roteador. O Homebrew mantém a configuração após remover ou reverter o CYTV. Se indisponível ou não confirmado, verifique o Homebrew e atualize o status. Veja o alcance dos testes no registro de aceitação.

[LG firmware blocking](../LG-FIRMWARE-UPDATES.md) · [1.2.0](../RELEASE-1.2.0-ACCEPTANCE.md)
