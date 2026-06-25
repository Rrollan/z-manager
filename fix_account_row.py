with open('src/components/accounts/AccountRow.tsx', 'r') as f:
    content = f.read()

# Remove the model extraction logic for claudeModel and gptModel
import re

content = re.sub(r"const claudeModel = [^;]+;", "", content)
content = re.sub(r"const gptModel = [^;]+;", "", content)

# Change glm5hModel to glm52Model
content = content.replace("const glm5hModel = account.quota?.models.find(m => m.name.toLowerCase().includes('glm-5.2 (5h)') || m.name.toLowerCase() === 'glm-5.2');", "const glm52Model = account.quota?.models.find(m => m.name === 'GLM-5.2');")

# Remove glmWeeklyModel definition if it existed, we'll redefine both
content = re.sub(r"const glmWeeklyModel = [^;]+;", "", content)

redef = """
    const glm52Model = account.quota?.models.find(m => m.name === 'GLM-5.2');
    const glmTurboModel = account.quota?.models.find(m => m.name === 'GLM-5-Turbo');
"""

# inject redef after `const { t } = useTranslation();`
idx = content.find("const { t } = useTranslation();")
if idx != -1:
    idx += len("const { t } = useTranslation();")
    content = content[:idx] + redef + content[idx:]

# In the render, there are blocks like `{/* Claude */}` and `{/* GPT */}` or similar.
# The user's screenshot had "proxy", "Кодов", etc. Wait!
# Let's just find the entire `<div className="grid grid-cols-2 gap-x-4 gap-y-1 py-0">` block and replace it!

start_div = content.find('<div className="grid grid-cols-2 gap-x-4 gap-y-1 py-0">')
if start_div != -1:
    end_div = content.find('</div>\n                )}', start_div)
    
    new_grid = """<div className="grid grid-cols-2 gap-x-4 gap-y-1 py-0">
                        {/* GLM-5.2 */}
                        <div className="relative h-[22px] flex items-center px-1.5 rounded-md overflow-hidden border border-gray-100/50 dark:border-white/5 bg-gray-50/30 dark:bg-white/5 group/quota">
                            {glm52Model && (
                                <div
                                    className={`absolute inset-y-0 left-0 transition-all duration-700 ease-out opacity-15 dark:opacity-20 ${getColorClass(glm52Model.percentage)}`}
                                    style={{ width: `${glm52Model.percentage}%` }}
                                />
                            )}
                            <div className="relative z-10 w-full flex items-center text-[10px] font-mono leading-none">
                                <span className="w-[64px] text-gray-500 dark:text-gray-400 font-bold pr-1 flex items-center gap-1" title="GLM 5.2">
                                    <span className="truncate">GLM-5.2</span>
                                </span>
                                <div className="flex-1 flex justify-center">
                                    {glm52Model?.reset_time ? (
                                        <span className={cn("flex items-center gap-0.5 font-medium transition-colors", getTimeColorClass(glm52Model.reset_time))}>
                                            <Clock className="w-2.5 h-2.5" />
                                            {formatTimeRemaining(glm52Model.reset_time)}
                                        </span>
                                    ) : (
                                        <span className="text-gray-300 dark:text-gray-600 italic scale-90">N/A</span>
                                    )}
                                </div>
                                <span className={cn("w-[36px] text-right font-bold transition-colors",
                                    getQuotaColor(glm52Model?.percentage || 0) === 'success' ? 'text-emerald-600 dark:text-emerald-400' :
                                        getQuotaColor(glm52Model?.percentage || 0) === 'warning' ? 'text-amber-600 dark:text-amber-400' : 'text-rose-600 dark:text-rose-400'
                                )}>
                                    {glm52Model ? `${glm52Model.percentage}%` : '-'}
                                </span>
                            </div>
                        </div>

                        {/* GLM-5-Turbo */}
                        <div className="relative h-[22px] flex items-center px-1.5 rounded-md overflow-hidden border border-gray-100/50 dark:border-white/5 bg-gray-50/30 dark:bg-white/5 group/quota">
                            {glmTurboModel && (
                                <div
                                    className={`absolute inset-y-0 left-0 transition-all duration-700 ease-out opacity-15 dark:opacity-20 ${getColorClass(glmTurboModel.percentage)}`}
                                    style={{ width: `${glmTurboModel.percentage}%` }}
                                />
                            )}
                            <div className="relative z-10 w-full flex items-center text-[10px] font-mono leading-none">
                                <span className="w-[64px] text-gray-500 dark:text-gray-400 font-bold pr-1 flex items-center gap-1" title="GLM 5 Turbo">
                                    <span className="truncate">5-Turbo</span>
                                </span>
                                <div className="flex-1 flex justify-center">
                                    {glmTurboModel?.reset_time ? (
                                        <span className={cn("flex items-center gap-0.5 font-medium transition-colors", getTimeColorClass(glmTurboModel.reset_time))}>
                                            <Clock className="w-2.5 h-2.5" />
                                            {formatTimeRemaining(glmTurboModel.reset_time)}
                                        </span>
                                    ) : (
                                        <span className="text-gray-300 dark:text-gray-600 italic scale-90">N/A</span>
                                    )}
                                </div>
                                <span className={cn("w-[36px] text-right font-bold transition-colors",
                                    getQuotaColor(glmTurboModel?.percentage || 0) === 'success' ? 'text-emerald-600 dark:text-emerald-400' :
                                        getQuotaColor(glmTurboModel?.percentage || 0) === 'warning' ? 'text-amber-600 dark:text-amber-400' : 'text-rose-600 dark:text-rose-400'
                                )}>
                                    {glmTurboModel ? `${glmTurboModel.percentage}%` : '-'}
                                </span>
                            </div>
                        </div>
                    </div>"""
    content = content[:start_div] + new_grid + content[end_div+6:]

with open('src/components/accounts/AccountRow.tsx', 'w') as f:
    f.write(content)
print("Patched AccountRow.tsx")
