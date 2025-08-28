import { redirect } from 'next/navigation'

export default function HomePage() {
  // Always start from the login screen; app will route post-login
  redirect('/login')
}
