"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
  {
    variants: {
      variant: {
        default:
          "bg-blue-600 text-white shadow-md hover:bg-blue-500 shadow-blue-500/20 hover:shadow-blue-500/35",
        destructive:
          "bg-rose-600 text-white hover:bg-rose-500 shadow-rose-500/20",
        outline:
          "border border-slate-700/80 bg-navy-900/60 text-slate-200 hover:bg-slate-800 hover:border-slate-600",
        secondary:
          "bg-slate-800 text-slate-100 hover:bg-slate-700/90 border border-slate-700/50",
        ghost:
          "text-slate-300 hover:bg-slate-800/60 hover:text-white",
        link: "text-blue-400 underline-offset-4 hover:underline",
        glow: "bg-gradient-to-r from-blue-600 to-cyan-500 text-white shadow-glow-blue hover:from-blue-500 hover:to-cyan-400",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-11 rounded-lg px-8 text-base",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };

