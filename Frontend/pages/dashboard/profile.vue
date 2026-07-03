<script setup>
definePageMeta({ middleware: "auth", layout: "dashboard" });
useSeoMeta({ title: "Profile | Booksall" });

const auth = useAuthStore();
const api = useApi();
const toast = useToast();
const user = computed(() => auth.user);

const initials = computed(() => {
    const n = user.value?.full_name || user.value?.email || "";
    return n.split(/[\s@.]+/).filter(Boolean).map((w) => w[0]).join("").slice(0, 2).toUpperCase() || "U";
});
const memberSince = computed(() => user.value ? new Date(user.value.date_joined).toLocaleDateString([], { month: "long", year: "numeric" }) : "");

// ---------- Avatar ----------
const avatarInput = ref(null);
const avatarUploading = ref(false);

async function onAvatarPicked(e) {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-picking the same file
    if (!file) return;
    if (!file.type.startsWith("image/")) {
        toast.add({ title: "Please pick an image file.", icon: "i-heroicons-exclamation-triangle", color: "red" });
        return;
    }
    if (file.size > 5 * 1024 * 1024) {
        toast.add({ title: "Image must be under 5 MB.", icon: "i-heroicons-exclamation-triangle", color: "red" });
        return;
    }
    const body = new FormData();
    body.append("avatar", file);
    avatarUploading.value = true;
    try {
        const updated = await api("/api/auth/me/", { method: "PATCH", body });
        auth.setUser(updated);
        toast.add({ title: "Profile picture updated", icon: "i-heroicons-check-circle", color: "green" });
    } catch (err) {
        toast.add({ title: apiErrorMessage(err), icon: "i-heroicons-exclamation-triangle", color: "red" });
    } finally {
        avatarUploading.value = false;
    }
}

async function removeAvatar() {
    avatarUploading.value = true;
    try {
        const updated = await api("/api/auth/me/", { method: "PATCH", body: { avatar: null } });
        auth.setUser(updated);
        toast.add({ title: "Profile picture removed", icon: "i-heroicons-trash", color: "green" });
    } catch (err) {
        toast.add({ title: apiErrorMessage(err), icon: "i-heroicons-exclamation-triangle", color: "red" });
    } finally {
        avatarUploading.value = false;
    }
}

// ---------- Personal info (name + phone) ----------
const info = reactive({ full_name: "", phone: "" });
const infoSaving = ref(false);
watch(user, (u) => {
    if (u) {
        info.full_name = u.full_name || "";
        info.phone = u.phone || "";
    }
}, { immediate: true });
const infoDirty = computed(() => user.value && (info.full_name !== (user.value.full_name || "") || info.phone !== (user.value.phone || "")));

async function saveInfo() {
    infoSaving.value = true;
    try {
        const updated = await api("/api/auth/me/", { method: "PATCH", body: { full_name: info.full_name, phone: info.phone } });
        auth.setUser(updated);
        toast.add({ title: "Profile updated", icon: "i-heroicons-check-circle", color: "green" });
    } catch (err) {
        toast.add({ title: apiErrorMessage(err), icon: "i-heroicons-exclamation-triangle", color: "red" });
    } finally {
        infoSaving.value = false;
    }
}

// ---------- Email ----------
const emailForm = reactive({ email: "" });
const emailSaving = ref(false);
const editingEmail = ref(false);
function startEmailEdit() {
    emailForm.email = user.value?.email || "";
    editingEmail.value = true;
}
async function saveEmail() {
    emailSaving.value = true;
    try {
        const updated = await api("/api/auth/me/", { method: "PATCH", body: { email: emailForm.email } });
        auth.setUser(updated);
        editingEmail.value = false;
        toast.add({ title: "Email updated", description: "We've sent a verification link to your new address.", icon: "i-heroicons-envelope", color: "green" });
    } catch (err) {
        toast.add({ title: apiErrorMessage(err), icon: "i-heroicons-exclamation-triangle", color: "red" });
    } finally {
        emailSaving.value = false;
    }
}

const resending = ref(false);
async function resendVerification() {
    resending.value = true;
    try {
        await api("/api/auth/resend-verification/", { method: "POST" });
        toast.add({ title: "Verification email sent", description: "Check your inbox.", icon: "i-heroicons-envelope", color: "green" });
    } catch (err) {
        toast.add({ title: apiErrorMessage(err), icon: "i-heroicons-exclamation-triangle", color: "red" });
    } finally {
        resending.value = false;
    }
}

// ---------- Password ----------
const pw = reactive({ current: "", next: "", confirm: "" });
const pwSaving = ref(false);
const pwError = computed(() => pw.next && pw.confirm && pw.next !== pw.confirm ? "Passwords do not match." : "");
const pwReady = computed(() => pw.current && pw.next && pw.next === pw.confirm);

async function changePassword() {
    if (!pwReady.value) return;
    pwSaving.value = true;
    try {
        await api("/api/auth/password-change/", { method: "POST", body: { current_password: pw.current, new_password: pw.next } });
        pw.current = pw.next = pw.confirm = "";
        toast.add({ title: "Password changed", icon: "i-heroicons-lock-closed", color: "green" });
    } catch (err) {
        toast.add({ title: apiErrorMessage(err), icon: "i-heroicons-exclamation-triangle", color: "red" });
    } finally {
        pwSaving.value = false;
    }
}
</script>

<template>
  <div class="max-w-3xl">
    <h1 class="font-display text-3xl font-bold text-[#f0f0f0] mb-2">Your profile</h1>
    <p class="text-[#888888] mb-8">Manage your personal details, contact info, and password.</p>

    <ClientOnly>
      <div v-if="user" class="space-y-6">
        <!-- Identity card -->
        <div class="relative overflow-hidden rounded-3xl border border-white/[0.06] bg-[#141414]">
          <!-- Decorative banner -->
          <div class="relative h-28 bg-[#161d08] overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-r from-[#c9ff47]/25 via-[#c9ff47]/10 to-transparent" />
            <div class="absolute -top-10 -right-10 w-48 h-48 rounded-full bg-[#c9ff47]/15 blur-2xl" />
            <div class="absolute inset-0" style="background-image: radial-gradient(rgba(201,255,71,0.12) 1px, transparent 1px); background-size: 18px 18px;" />
          </div>

          <div class="px-6 pb-6 sm:px-8">
            <div class="flex flex-col sm:flex-row sm:items-end gap-5 -mt-12">
              <!-- Avatar + upload -->
              <div class="relative shrink-0 w-24 h-24">
                <img
                  v-if="user.avatar"
                  :src="user.avatar"
                  :alt="user.full_name || 'Profile picture'"
                  class="w-24 h-24 rounded-2xl object-cover ring-4 ring-[#141414] shadow-lg"
                />
                <div v-else class="w-24 h-24 rounded-2xl bg-[#c9ff47] text-black grid place-items-center text-3xl font-display font-bold ring-4 ring-[#141414] shadow-lg">
                  {{ initials }}
                </div>
                <button
                  type="button"
                  class="absolute inset-0 rounded-2xl grid place-items-center bg-black/55 opacity-0 hover:opacity-100 focus-visible:opacity-100 transition-opacity"
                  :disabled="avatarUploading"
                  aria-label="Change profile picture"
                  @click="avatarInput?.click()"
                >
                  <UIcon :name="avatarUploading ? 'i-heroicons-arrow-path' : 'i-heroicons-camera'" class="text-2xl text-white" :class="avatarUploading ? 'animate-spin' : ''" />
                </button>
                <input ref="avatarInput" type="file" accept="image/*" class="hidden" @change="onAvatarPicked" />
              </div>

              <div class="flex-1 min-w-0 sm:pb-1">
                <h2 class="font-display text-2xl font-bold text-[#f0f0f0] truncate">{{ user.full_name || "Player" }}</h2>
                <p class="text-sm text-[#888888] mt-0.5">
                  <UIcon name="i-heroicons-calendar" class="align-text-bottom" />
                  Member since {{ memberSince }}
                </p>
              </div>

              <div class="flex gap-2 sm:pb-1">
                <UButton color="gray" variant="soft" size="xs" icon="i-heroicons-camera" :loading="avatarUploading" @click="avatarInput?.click()">
                  {{ user.avatar ? "Change photo" : "Add photo" }}
                </UButton>
                <UButton v-if="user.avatar" color="red" variant="ghost" size="xs" icon="i-heroicons-trash" :disabled="avatarUploading" @click="removeAvatar">
                  Remove
                </UButton>
              </div>
            </div>

            <!-- Verification chips -->
            <div class="mt-5 flex flex-wrap gap-2 border-t border-white/[0.06] pt-4">
              <span
                class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold"
                :class="user.is_email_verified ? 'bg-emerald-400/10 text-emerald-400' : 'bg-amber-400/10 text-amber-400'"
              >
                <UIcon :name="user.is_email_verified ? 'i-heroicons-check-badge' : 'i-heroicons-exclamation-circle'" />
                {{ user.is_email_verified ? "Email verified" : "Email unverified" }}
              </span>
              <span
                class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold"
                :class="user.is_phone_verified ? 'bg-emerald-400/10 text-emerald-400' : 'bg-white/5 text-[#8f8f8f]'"
              >
                <UIcon :name="user.is_phone_verified ? 'i-heroicons-check-badge' : 'i-heroicons-device-phone-mobile'" />
                {{ user.is_phone_verified ? "Phone verified" : "Phone not verified" }}
              </span>
            </div>
          </div>
        </div>

        <!-- Personal info -->
        <div class="rounded-3xl border border-white/[0.06] bg-[#141414] p-6">
          <div class="flex items-center gap-3 mb-5">
            <div class="w-10 h-10 rounded-xl bg-[#1e1e1e] grid place-items-center text-[#c9ff47]">
              <UIcon name="i-heroicons-user" class="text-xl" />
            </div>
            <div>
              <h3 class="font-display font-semibold text-[#f0f0f0]">Personal info</h3>
              <p class="text-xs text-[#888888]">Your name and mobile number.</p>
            </div>
          </div>
          <form class="grid sm:grid-cols-2 gap-4" @submit.prevent="saveInfo">
            <UFormGroup label="Full name">
              <UInput v-model="info.full_name" placeholder="Your name" icon="i-heroicons-user" />
            </UFormGroup>
            <UFormGroup label="Mobile number" :hint="user.is_phone_verified ? 'Changing it will require re-verification' : ''">
              <UInput v-model="info.phone" placeholder="98XXXXXXXX" icon="i-heroicons-device-phone-mobile" />
            </UFormGroup>
            <div class="sm:col-span-2 flex justify-end">
              <UButton type="submit" color="primary" :loading="infoSaving" :disabled="!infoDirty">
                Save changes
              </UButton>
            </div>
          </form>
        </div>

        <!-- Email -->
        <div class="rounded-3xl border border-white/[0.06] bg-[#141414] p-6">
          <div class="flex items-center gap-3 mb-5">
            <div class="w-10 h-10 rounded-xl bg-[#1e1e1e] grid place-items-center text-[#c9ff47]">
              <UIcon name="i-heroicons-envelope" class="text-xl" />
            </div>
            <div>
              <h3 class="font-display font-semibold text-[#f0f0f0]">Email address</h3>
              <p class="text-xs text-[#888888]">Used to sign in and for booking updates.</p>
            </div>
          </div>

          <div v-if="!editingEmail" class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-2 min-w-0">
              <p class="font-medium text-[#f0f0f0] truncate">{{ user.email }}</p>
              <UBadge :color="user.is_email_verified ? 'green' : 'amber'" variant="subtle" size="xs">
                {{ user.is_email_verified ? "Verified" : "Unverified" }}
              </UBadge>
            </div>
            <div class="flex gap-2">
              <UButton
                v-if="!user.is_email_verified"
                color="amber" variant="soft" size="sm"
                icon="i-heroicons-paper-airplane"
                :loading="resending"
                @click="resendVerification"
              >
                Resend verification
              </UButton>
              <UButton color="gray" variant="soft" size="sm" icon="i-heroicons-pencil-square" @click="startEmailEdit">
                Change email
              </UButton>
            </div>
          </div>

          <form v-else class="space-y-4" @submit.prevent="saveEmail">
            <UAlert
              icon="i-heroicons-exclamation-triangle"
              color="amber"
              variant="subtle"
              title="You'll need to verify your new address"
              description="A verification link will be sent to the new email. You'll keep signing in with the new address."
            />
            <UFormGroup label="New email address">
              <UInput v-model="emailForm.email" type="email" placeholder="you@example.com" icon="i-heroicons-envelope" required />
            </UFormGroup>
            <div class="flex justify-end gap-2">
              <UButton color="gray" variant="ghost" @click="editingEmail = false">Cancel</UButton>
              <UButton type="submit" color="primary" :loading="emailSaving" :disabled="!emailForm.email || emailForm.email === user.email">
                Update email
              </UButton>
            </div>
          </form>
        </div>

        <!-- Password -->
        <div class="rounded-3xl border border-white/[0.06] bg-[#141414] p-6">
          <div class="flex items-center gap-3 mb-5">
            <div class="w-10 h-10 rounded-xl bg-[#1e1e1e] grid place-items-center text-[#c9ff47]">
              <UIcon name="i-heroicons-lock-closed" class="text-xl" />
            </div>
            <div>
              <h3 class="font-display font-semibold text-[#f0f0f0]">Password</h3>
              <p class="text-xs text-[#888888]">Use at least 8 characters. Avoid reusing old passwords.</p>
            </div>
          </div>
          <form class="grid sm:grid-cols-2 gap-4" @submit.prevent="changePassword">
            <UFormGroup label="Current password" class="sm:col-span-2">
              <UInput v-model="pw.current" type="password" placeholder="••••••••" icon="i-heroicons-key" autocomplete="current-password" />
            </UFormGroup>
            <UFormGroup label="New password">
              <UInput v-model="pw.next" type="password" placeholder="••••••••" icon="i-heroicons-lock-closed" autocomplete="new-password" />
            </UFormGroup>
            <UFormGroup label="Confirm new password" :error="pwError">
              <UInput v-model="pw.confirm" type="password" placeholder="••••••••" icon="i-heroicons-lock-closed" autocomplete="new-password" />
            </UFormGroup>
            <div class="sm:col-span-2 flex justify-end">
              <UButton type="submit" color="primary" :loading="pwSaving" :disabled="!pwReady">
                Change password
              </UButton>
            </div>
          </form>
        </div>

        <!-- Quick links -->
        <div class="flex flex-wrap gap-3">
          <UButton to="/dashboard/bookings" color="primary" variant="soft" icon="i-heroicons-calendar-days">My bookings</UButton>
          <UButton to="/manage" color="gray" variant="soft" icon="i-heroicons-building-storefront">Manage venues</UButton>
          <UButton to="/teams" color="gray" variant="soft" icon="i-heroicons-user-group">My teams</UButton>
        </div>
      </div>

      <div v-else class="space-y-4">
        <USkeleton class="h-40 rounded-3xl" />
        <USkeleton class="h-56 rounded-3xl" />
        <USkeleton class="h-40 rounded-3xl" />
      </div>
    </ClientOnly>
  </div>
</template>
