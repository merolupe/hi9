@echo off
title Central Fiscal - Hinove
cd /d "%~dp0"

rem ---------------------------------------------------------------------
rem  Central de Ferramentas Fiscais - Hinove Agrociencia S.A.
rem
rem  De dois cliques neste arquivo. Ele abre a Central no navegador, com
rem  as ferramentas do setor para escolher: Apurabot, DiXML e as demais
rem  conforme forem entrando.
rem
rem  Nao instala nada, nao baixa nada e nao cria programa novo: usa o
rem  Python que ja esta na maquina, e as bibliotecas viajam junto com o
rem  codigo, em vendor. Por isso funciona sem privilegio de administrador.
rem
rem  Uma maquina costuma ter mais de um Python. Aqui nao se escolhe por
rem  nome: pergunta-se a cada um se ele consegue rodar, com verificar.py.
rem
rem  Esta janela preta precisa continuar aberta enquanto voce usa as
rem  ferramentas. Fechar esta janela encerra a Central.
rem ---------------------------------------------------------------------

set "PY="
for %%C in ("python" "py -3" "py" "python3") do (
  if not defined PY %%~C verificar.py >nul 2>nul && set "PY=%%~C"
)

if defined PY goto :rodar

echo.
echo  Nenhum Python desta maquina consegue rodar as ferramentas.
echo.
echo  Duas causas possiveis:
echo.
echo   1. Nao ha Python instalado, ou ele e anterior ao 3.10.
echo      Peca a instalacao do Python 3.10 ou mais novo. A opcao
echo      "somente para este usuario" nao exige administrador.
echo.
echo   2. A pasta veio incompleta.
echo      Baixe o ZIP de novo e extraia inteiro, sem tirar nada.
echo.
echo  Para ver a mensagem detalhada, abra o prompt de comando nesta
echo  pasta e rode:   python verificar.py
echo.
pause
exit /b 1

:rodar
%PY% rodar.py
if errorlevel 1 (
  echo.
  echo  A Central terminou com erro. A mensagem esta acima.
  echo.
  pause
)
