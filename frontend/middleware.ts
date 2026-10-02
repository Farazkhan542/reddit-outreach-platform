import { NextResponse, type NextRequest } from "next/server";

import { TOKEN_COOKIE, decodeRole } from "@/lib/api";

// Role-based route gating for the single app. The API enforces permissions independently.
export function middleware(req: NextRequest) {
  const token = req.cookies.get(TOKEN_COOKIE)?.value;
  const role = token ? decodeRole(token) : null;
  const { pathname } = req.nextUrl;

  if (!role) return NextResponse.redirect(new URL("/login", req.url));

  const home = role === "member" ? "/member" : "/admin";
  if (pathname === "/" || (pathname.startsWith("/admin") && role === "member")) {
    return NextResponse.redirect(new URL(home, req.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/", "/admin/:path*", "/member/:path*"] };
