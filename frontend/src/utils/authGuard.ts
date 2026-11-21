export function authGuard(): boolean {
    const token = localStorage.getItem('access_token')?.trim();
    return token ? true : redirectToLogin();
}

function redirectToLogin(): false {
    window.location.assign('/');
    return false;
}
