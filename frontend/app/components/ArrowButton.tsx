'use client'

interface ArrowButtonProps {
  onClick: () => void
  disabled?: boolean
}

export default function ArrowButton({ onClick, disabled }: ArrowButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="group flex items-center justify-center w-16 h-16 rounded-full border-2 border-blue-500 hover:bg-blue-500 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed animate-float"
    >
      <svg
        className="w-8 h-8 text-blue-500 group-hover:text-white transition-colors duration-300"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 5l7 7-7 7"
        />
      </svg>
    </button>
  )
}


