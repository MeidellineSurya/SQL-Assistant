import { NextResponse, type NextRequest } from "next/server";

// This is a UX-level redirect only: it checks for a presence cookie, not a
// verified JWT (the real access/refresh tokens live in localStorage, which
// proxy can't read). The backend is what actually rejects invalid or
// expired tokens on every request — this just avoids flashing a protected
// page before the client-side check kicks in.
export function proxy(request: NextRequest) {
  const hasSession = request.cookies.has("has_session");
  const { pathname } = request.nextUrl;

  const isAuthPage = pathname.startsWith("/login") || pathname.startsWith("/register");

  if (!hasSession && !isAuthPage) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (hasSession && isAuthPage) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/connections/:path*", "/login", "/register"],
};
