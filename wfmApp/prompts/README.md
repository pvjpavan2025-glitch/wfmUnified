# Field Service Dashboard

A modern field service management dashboard built with Next.js, TypeScript, and Tailwind CSS. This application provides a user interface for managing field service operations.

## Features

- 📱 Responsive design with mobile support
- 🎨 Modern UI components using Radix UI
- 🌙 Dark/Light mode support
- 📊 Data visualization with Recharts
- 🔒 Protected routes with authentication
- ⚡ Fast page loads with Next.js

## Tech Stack

- [Next.js](https://nextjs.org/) - React framework for production
- [TypeScript](https://www.typescriptlang.org/) - Static type checking
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [Radix UI](https://www.radix-ui.com/) - Unstyled, accessible components
- [Recharts](https://recharts.org/) - Composable charting library
- [React Hook Form](https://react-hook-form.com/) - Form validation
- [Zod](https://zod.dev/) - TypeScript-first schema validation

## Getting Started

### Prerequisites

- Node.js (version 16 or higher)
- npm or yarn or pnpm

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd field-service-dashboard
```

2. Install dependencies
```bash
npm install --legacy-peer-deps
```

3. Start the development server
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
├── app/                  # Next.js app directory
│   ├── dashboard/       # Dashboard pages
│   ├── login/          # Authentication pages
│   └── layout.tsx      # Root layout
├── components/          # React components
│   ├── ui/            # Reusable UI components
│   └── dashboard/     # Dashboard-specific components
├── contexts/           # React contexts
├── hooks/              # Custom React hooks
├── lib/               # Utility functions
└── public/            # Static assets
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
