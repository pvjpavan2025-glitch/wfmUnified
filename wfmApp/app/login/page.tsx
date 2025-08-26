import LoginClient from '@/app/login/LoginClient'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export default function LoginPage() {
  return <LoginClient />
}
