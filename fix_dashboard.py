with open('src/pages/Dashboard.tsx', 'r') as f:
    content = f.read()

# Replace get5hQuota, getWeeklyQuota, getMcpQuota with getGlm52Quota and getGlmTurboQuota
content = content.replace("const get5hQuota = (a: Account) => {", "const getGlm52Quota = (a: Account) => {")
content = content.replace("m.name === 'GLM-5.2 (5h)' || m.name === 'glm-5.2'", "m.name === 'GLM-5.2'")

content = content.replace("const getWeeklyQuota = (a: Account) => {", "const getGlmTurboQuota = (a: Account) => {")
content = content.replace("m.name === 'GLM-5.2 (Weekly)'", "m.name === 'GLM-5-Turbo'")

content = content.replace("quotas5h", "quotasGlm52")
content = content.replace("quotasWeekly", "quotasGlmTurbo")

content = content.replace("get5hQuota(a)", "getGlm52Quota(a)")
content = content.replace("getWeeklyQuota(a)", "getGlmTurboQuota(a)")

content = content.replace("avg5h:", "avgGlm52:")
content = content.replace("avgWeekly:", "avgGlmTurbo:")

content = content.replace("stats.avg5h", "stats.avgGlm52")
content = content.replace("stats.avgWeekly", "stats.avgGlmTurbo")

content = content.replace("Avg 5h Token Limit", "Avg GLM-5.2 Limit")
content = content.replace("Avg Weekly Token Limit", "Avg GLM-5-Turbo Limit")

with open('src/pages/Dashboard.tsx', 'w') as f:
    f.write(content)

print("Patched Dashboard.tsx")
