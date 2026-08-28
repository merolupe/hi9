@echo off
title Apurabot
cd /d "%~dp0"

rem ---------------------------------------------------------------------
rem  Apurabot - apuracao de ICMS
rem
rem  De dois cliques neste arquivo. Ele abre o Apurabot no navegador.
rem
rem  Nao instala nada e nao cria programa novo: usa o Python que ja esta
rem  na maquina. Por isso funciona sem privilegio de administrador.
rem
rem  Uma maquina costuma ter mais de um Python, e as bibliotecas ficam em
rem  um deles so. Por isso aqui nao se escolhe por nome: testa-se cada
rem  candidato ate achar o que consegue importar as tres bibliotecas.
rem
rem  Esta janela preta precisa continuar aberta enquanto voce usa a
rem  ferramenta. Fechar esta janela encerra o Apurabot.
rem ---------------------------------------------------------------------

set "PY="
for %%C in ("python" "py -3" "py" "python3") do (
  if not defined PY (
    %%~C -c "import yaml, openpyxl, xlrd" >nul 2>nul && set "PY=%%~C"
  )
)

if defined PY goto :rodar

echo.
echo  O Apurabot precisa de tres bibliotecas: openpyxl, xlrd e PyYAML.
echo  Nenhum Python desta maquina tem as tres.
echo.
echo  A maquina costuma ter mais de um Python instalado, e um `pip install`
echo  sozinho pode instalar em outro que nao o que o Apurabot usa. Foi
echo  provavelmente o que aconteceu.
echo.
echo  Para resolver, rode AS DUAS linhas abaixo no prompt de comando:
echo.
echo     python -m pip install --user openpyxl "xlrd==2.0.1" PyYAML
echo     py -3 -m pip install --user openpyxl "xlrd==2.0.1" PyYAML
echo.
echo  Uma delas pode responder que o comando nao existe. Tudo bem: e sinal
echo  de que aquele Python nao esta instalado aqui. O que importa e que as
echo  bibliotecas fiquem em todos os que existem.
echo.
echo  Se as duas responderem que o comando nao existe, o Python nao esta
echo  instalado. Peca a instalacao do Python 3.10 ou superior - a opcao
echo  "somente para este usuario" nao exige privilegio de administrador.
echo.
pause
exit /b 1

:rodar
%PY% rodar.py janela
if errorlevel 1 (
  echo.
  echo  O Apurabot terminou com erro. A mensagem esta acima.
  echo.
  pause
)
