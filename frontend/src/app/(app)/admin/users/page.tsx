"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { admin, type AdminUser } from "@/lib/api";
import type { UserRole } from "@/lib/types";
import { useAuthStore } from "@/store/auth";

export default function AdminUsersPage() {
  const router = useRouter();
  const me = useAuthStore((s) => s.user);
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<AdminUser | null>(null);

  // Client-side admin gate. The backend enforces 403 anyway, but this avoids
  // a flash of the form for non-admin users.
  useEffect(() => {
    if (me && me.role !== "ADMIN") router.replace("/dashboard");
  }, [me, router]);

  const list = useQuery({
    queryKey: ["admin", "users"],
    queryFn: () => admin.listUsers(),
    enabled: me?.role === "ADMIN",
  });

  if (!me || me.role !== "ADMIN") return null;

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <h1 style={{ margin: 0 }}>Users</h1>
        <button className="qp-btn" onClick={() => setShowCreate(true)}>
          New user
        </button>
      </div>

      <div className="qp-card" style={{ padding: 0 }}>
        {list.isLoading ? (
          <p style={{ padding: 16 }}>Loading...</p>
        ) : (
          <table className="qp-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {list.data?.map((u) => {
                const isMe = u.id === me?.id;
                return (
                  <tr key={u.id}>
                    <td>
                      {u.name}
                      {isMe ? (
                        <span
                          style={{
                            marginLeft: 6,
                            color: "var(--color-muted)",
                            fontSize: "0.8rem",
                          }}
                        >
                          (you)
                        </span>
                      ) : null}
                    </td>
                    <td style={{ color: "var(--color-muted)" }}>{u.email}</td>
                    <td>
                      <span className="qp-role">{u.role}</span>
                    </td>
                    <td>
                      <span
                        className={
                          u.is_active
                            ? "qp-status qp-status-strong"
                            : "qp-status qp-status-not_started"
                        }
                      >
                        {u.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td>
                      <button
                        className="qp-btn-ghost"
                        onClick={() => setEditing(u)}
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {showCreate ? (
        <CreateUserModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            qc.invalidateQueries({ queryKey: ["admin", "users"] });
          }}
        />
      ) : null}

      {editing ? (
        <EditUserModal
          user={editing}
          isSelf={editing.id === me?.id}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            qc.invalidateQueries({ queryKey: ["admin", "users"] });
          }}
        />
      ) : null}
    </div>
  );
}

function CreateUserModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("TEACHER");

  const mutation = useMutation({
    mutationFn: () => admin.createUser({ name, email, password, role }),
    onSuccess: onCreated,
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  return (
    <div className="qp-overlay" onClick={onClose}>
      <div className="qp-modal" onClick={(e) => e.stopPropagation()}>
        <h2>New user</h2>
        <form onSubmit={handleSubmit} className="qp-form">
          <div>
            <label>Full name</label>
            <input required value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label>Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label>Initial password (min 8 chars)</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div>
            <label>Role</label>
            <select value={role} onChange={(e) => setRole(e.target.value as UserRole)}>
              <option value="TEACHER">Teacher</option>
              <option value="ADMIN">Admin</option>
            </select>
          </div>
          {mutation.error ? (
            <div className="qp-error">{(mutation.error as Error).message}</div>
          ) : null}
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button type="button" className="qp-btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="qp-btn" disabled={mutation.isPending}>
              {mutation.isPending ? "Creating..." : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EditUserModal({
  user,
  isSelf,
  onClose,
  onSaved,
}: {
  user: AdminUser;
  isSelf: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState(user.name);
  const [role, setRole] = useState<UserRole>(user.role);
  const [isActive, setIsActive] = useState<boolean>(user.is_active);
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: () => {
      const data: Partial<{ name: string; role: UserRole; is_active: boolean; password: string }> = {};
      if (name !== user.name) data.name = name;
      if (role !== user.role) data.role = role;
      if (isActive !== user.is_active) data.is_active = isActive;
      if (password) data.password = password;
      return admin.updateUser(user.id, data);
    },
    onSuccess: onSaved,
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  return (
    <div className="qp-overlay" onClick={onClose}>
      <div className="qp-modal" onClick={(e) => e.stopPropagation()}>
        <h2>Edit {user.email}</h2>
        {isSelf ? (
          <p style={{ color: "var(--color-muted)", marginTop: 0 }}>
            Self-protection: you cannot change your own role or deactivate
            yourself.
          </p>
        ) : null}
        <form onSubmit={handleSubmit} className="qp-form">
          <div>
            <label>Full name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label>Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              disabled={isSelf}
            >
              <option value="TEACHER">Teacher</option>
              <option value="ADMIN">Admin</option>
            </select>
          </div>
          <div>
            <label>
              <input
                type="checkbox"
                checked={isActive}
                disabled={isSelf}
                onChange={(e) => setIsActive(e.target.checked)}
                style={{ width: "auto", marginRight: 8 }}
              />
              Active
            </label>
          </div>
          <div>
            <label>New password (leave blank to keep current)</label>
            <input
              type="password"
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>
          {mutation.error ? (
            <div className="qp-error">{(mutation.error as Error).message}</div>
          ) : null}
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button type="button" className="qp-btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="qp-btn" disabled={mutation.isPending}>
              {mutation.isPending ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
