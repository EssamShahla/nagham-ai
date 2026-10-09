"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Mail, Lock, User } from "lucide-react"

import { AuthShell } from "@/components/auth-shell"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { api, ApiError, formatValidationError } from "@/lib/api"
import type { UserResponse } from "@/lib/types"

const INSTRUMENTS = [
  "Oud",
  "Qanun",
  "Nay",
  "Violin",
  "Buzuq",
  "Percussion",
  "Vocals",
  "Other",
]

const ROLES = [
  "Performer",
  "Composer",
  "Student",
  "Teacher",
  "Researcher",
  "Listener",
]

export default function RegisterPage() {
  const router = useRouter()

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleRegister = async (
    e: React.FormEvent<HTMLFormElement>
  ) => {
    e.preventDefault()

    setLoading(true)
    setError("")

    const formData = new FormData(e.currentTarget)

    const data = {
      name: formData.get("name"),
      email: formData.get("email"),
      password: formData.get("password"),
      instrument: formData.get("instrument"),
      music_role: formData.get("music_role"),
    }

    try {
      await api<UserResponse>("/auth/register", {
        method: "POST",
        body: data,
      })

      // Save the email temporarily so the verification
      // page knows which account should be verified.
      localStorage.setItem(
        "verification_email",
        String(data.email)
      )

      router.push("/verify")
    } catch (err) {
      if (err instanceof ApiError) {
        setError(
          err.status === 422
            ? formatValidationError(err.detail)
            : typeof err.detail === "string"
              ? err.detail
              : "Registration failed"
        )
      } else {
        setError("Something went wrong. Please try again.")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      quote={{
        text: "Every maqam is a door; behind each one waits a different feeling.",
        source: "On the art of tarab",
      }}
    >
      <h1 className="font-display text-3xl font-semibold">
        Create your account
      </h1>

      <p className="mt-2 text-sm text-muted-foreground">
        Join the community and start discovering repertoire.
      </p>

      <form
        onSubmit={handleRegister}
        className="mt-8 flex flex-col gap-5"
      >
        {/* Full name */}
        <div>
          <Label htmlFor="name">Full name</Label>

          <div className="relative">
            <User className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />

            <Input
              id="name"
              name="name"
              placeholder="Your name"
              className="pl-9"
              required
            />
          </div>
        </div>

        {/* Email */}
        <div>
          <Label htmlFor="email">Email</Label>

          <div className="relative">
            <Mail className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />

            <Input
              id="email"
              name="email"
              type="email"
              placeholder="you@example.com"
              className="pl-9"
              required
            />
          </div>
        </div>

        {/* Instrument + Role */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="instrument">
              Instrument
            </Label>

            <Select
              id="instrument"
              name="instrument"
              defaultValue="Oud"
              required
            >
              {INSTRUMENTS.map((instrument) => (
                <option
                  key={instrument}
                  value={instrument}
                >
                  {instrument}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <Label htmlFor="music_role">
              Role
            </Label>

            <Select
              id="music_role"
              name="music_role"
              defaultValue="Performer"
            >
              {ROLES.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </Select>
          </div>
        </div>

        {/* Password */}
        <div>
          <Label htmlFor="password">
            Password
          </Label>

          <div className="relative">
            <Lock className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />

            <Input
              id="password"
              name="password"
              type="password"
              placeholder="Create a password"
              className="pl-9"
              minLength={6}
              required
            />
          </div>
        </div>

        {/* Error message */}
        {error && (
          <p className="text-sm text-red-500">
            {error}
          </p>
        )}

        {/* Submit */}
        <Button
          type="submit"
          disabled={loading}
          className="mt-1 h-11 w-full text-sm"
        >
          {loading
            ? "Creating account..."
            : "Create account"}
        </Button>
      </form>

      <p className="mt-8 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-medium text-gold hover:underline"
        >
          Sign in
        </Link>
      </p>
    </AuthShell>
  )
}