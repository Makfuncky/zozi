"use client";

import { Logo as SharedLogo, type LogoSize } from "@shared/logo/web";

interface LogoProps {
	size?: LogoSize;
	className?: string;
	animated?: boolean;
	showWordmark?: boolean;
}

export default function Logo({ size = "md", className, animated = true, showWordmark = true }: LogoProps) {
	return (
		<SharedLogo
			size={size}
			className={className}
			animated={animated}
			showWordmark={showWordmark}
		/>
	);
}


