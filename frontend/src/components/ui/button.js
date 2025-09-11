import React from "react"
import { cn } from "../../lib/utils"

const Button = React.forwardRef(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    const variants = {
      default: "bg-primary text-primary-foreground hover:bg-primary/90",
      destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
      outline: "border border-slate-600 bg-transparent text-slate-300 hover:bg-slate-700 hover:text-white",
      secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
      ghost: "text-slate-400 hover:bg-slate-700 hover:text-white",
      link: "text-primary underline-offset-4 hover:underline",
      anime: "bg-gradient-to-r from-anime-pink to-anime-purple text-white hover:from-anime-purple hover:to-anime-blue transform hover:scale-105 transition-all duration-300"
    }

    const sizes = {
      default: "h-10 px-4 py-2",
      sm: "h-9 rounded-md px-3",
      lg: "h-11 rounded-md px-8",
      icon: "h-10 w-10"
    }

    return (
      <button
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 cursor-pointer relative z-10",
          variants[variant],
          sizes[size],
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
