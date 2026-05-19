Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batchFile = """" & scriptDir & "\apply_jobs.bat"""

value = InputBox("How many jobs do you want to apply for?", "Naukri Apply", "5")

If value = "" Then
    WScript.Quit
End If

If Not IsNumeric(value) Then
    MsgBox "Please enter a whole number like 1, 5, or 10.", vbExclamation, "Invalid Number"
    WScript.Quit
End If

If CLng(value) < 0 Then
    MsgBox "Please enter 0 or a positive whole number.", vbExclamation, "Invalid Number"
    WScript.Quit
End If

shell.Run batchFile & " " & CLng(value), 1, False
