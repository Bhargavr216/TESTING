Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batchFile = """" & scriptDir & "\daily_auto.bat"""

' Run hidden (0) and don't wait (False)
shell.Run batchFile, 0, False


