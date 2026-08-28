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
rem  Esta janela preta precisa continuar aberta enquanto voce usa a
rem  ferramenta. Fechar esta janela encerra o Apurabot.
rem ---------------------------------------------------------------------

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"

if not defined PY (
  echo.
  echo  O Python nao foi encontrado nesta maquina.
  echo.
  echo  O Apurabot precisa dele. Peca a instalacao do Python 3.10 ou
  echo  superior - a instalacao "somente para este usuario" nao exige
  echo  privilegio de administrador.
  echo.
  pause
  exit /b 1
)

%PY% rodar.py janela
if errorlevel 1 (
  echo.
  echo  O Apurabot terminou com erro. A mensagem esta acima.
  echo.
  pause
)
