"use client";

import Image from "next/image";
import Link from "next/link";
import { MobileSidebar } from "./forum/Sidebar";

export function Header() {
  return (
    <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-4 lg:h-[60px] lg:px-6">
      <div className="md:hidden">
        <MobileSidebar />
      </div>
      <div className="w-full flex-1 flex justify-between items-center">
        <Link
          href="/"
          className="flex flex-col gap-x-3 md:flex-row items-center gap-2"
        >
          <Image
            src="/cow-ai-logo.png"
            alt="CoW AI"
            width={40}
            height={40}
            className="h-8 w-8 md:h-9 md:w-9 rounded-full object-cover"
          />
          <span className="text-base font-semibold text-cow">CoW AI</span>
        </Link>
      </div>
    </header>
  );
}
