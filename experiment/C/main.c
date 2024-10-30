#include <Windows.h>

int main() {
    // Load the LogonUI.dll module
    HMODULE hModule = LoadLibraryA("C:\\Windows\\System32\\LogonUI.dll");

    if (hModule != NULL) {
        // Get the address of the LogonUser function
        FARPROC pfnLogonUser = GetProcAddress(hModule, "LogonUserW");

        if (pfnLogonUser != NULL) {
            // Simulate a login attempt (not recommended)
            // This is for demonstration purposes only and should not be used in production code.
            int result = ((int(*)())pfnLogonUser)("username", "password", 0, 0);
        }

        FreeLibrary(hModule);
    } else {
        // DLL がロードできない場合にエラーを表示する
        printf("DLL のロードに失敗しました。\n");
    }

    return 0;
}
