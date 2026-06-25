import { TrendingUp } from 'lucide-react';
import { Account } from '../../types/account';

interface BestAccountsProps {
    accounts: Account[];
    currentAccountId?: string;
    onSwitch?: (accountId: string) => void;
}

import { useTranslation } from 'react-i18next';

function BestAccounts({ accounts, currentAccountId, onSwitch }: BestAccountsProps) {
    const { t } = useTranslation();
    const glm52Sorted = accounts
        .filter(a => a.id !== currentAccountId)
        .map(a => {
            const quota = a.quota?.models.find(m => m.name.toLowerCase() === 'glm-5.2')?.percentage || 0;
            return {
                ...a,
                quotaVal: quota,
            };
        })
        .filter(a => a.quotaVal > 0)
        .sort((a, b) => b.quotaVal - a.quotaVal);

    const glm5TurboSorted = accounts
        .filter(a => a.id !== currentAccountId)
        .map(a => ({
            ...a,
            quotaVal: a.quota?.models.find(m => m.name.toLowerCase() === 'glm-5-turbo')?.percentage || 0,
        }))
        .filter(a => a.quotaVal > 0)
        .sort((a, b) => b.quotaVal - a.quotaVal);

    let bestGlm52 = glm52Sorted[0];
    let bestGlm5Turbo = glm5TurboSorted[0];

    // 2. 如果推荐是同一个账号，且有其他选择，尝试寻找最优的"不同账号"组合
    if (bestGlm52 && bestGlm5Turbo && bestGlm52.id === bestGlm5Turbo.id) {
        const nextGlm52 = glm52Sorted[1];
        const nextGlm5Turbo = glm5TurboSorted[1];

        const scoreA = bestGlm52.quotaVal + (nextGlm5Turbo?.quotaVal || 0);
        const scoreB = (nextGlm52?.quotaVal || 0) + bestGlm5Turbo.quotaVal;

        if (nextGlm5Turbo && (!nextGlm52 || scoreA >= scoreB)) {
            bestGlm5Turbo = nextGlm5Turbo;
        } else if (nextGlm52) {
            bestGlm52 = nextGlm52;
        }
    }

    const bestGlm52Render = bestGlm52 ? { ...bestGlm52, glm52Quota: bestGlm52.quotaVal } : undefined;
    const bestGlm5TurboRender = bestGlm5Turbo ? { ...bestGlm5Turbo, glm5TurboQuota: bestGlm5Turbo.quotaVal } : undefined;

    return (
        <div className="bg-white dark:bg-base-100 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-base-200 h-full flex flex-col">
            <h2 className="text-base font-semibold text-gray-900 dark:text-base-content mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-500 dark:text-blue-400" />
                {t('dashboard.best_accounts')}
            </h2>

            <div className="space-y-2 flex-1">
                {/* GLM-5.2 最佳 */}
                {bestGlm52Render && (
                    <div className="flex items-center justify-between p-2.5 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-100 dark:border-green-900/30">
                        <div className="flex-1 min-w-0">
                            <div className="text-[10px] text-green-600 dark:text-green-400 font-medium mb-0.5">GLM-5.2</div>
                            <div className="font-medium text-sm text-gray-900 dark:text-base-content truncate">
                                {bestGlm52Render.email}
                            </div>
                        </div>
                        <div className="ml-2 px-2 py-0.5 bg-green-500 text-white text-xs font-semibold rounded-full">
                            {bestGlm52Render.glm52Quota}
                        </div>
                    </div>
                )}

                {/* GLM-5-Turbo 最佳 */}
                {bestGlm5TurboRender && (
                    <div className="flex items-center justify-between p-2.5 bg-cyan-50 dark:bg-cyan-900/20 rounded-lg border border-cyan-100 dark:border-cyan-900/30">
                        <div className="flex-1 min-w-0">
                            <div className="text-[10px] text-cyan-600 dark:text-cyan-400 font-medium mb-0.5">GLM-5-Turbo</div>
                            <div className="font-medium text-sm text-gray-900 dark:text-base-content truncate">
                                {bestGlm5TurboRender.email}
                            </div>
                        </div>
                        <div className="ml-2 px-2 py-0.5 bg-cyan-500 text-white text-xs font-semibold rounded-full">
                            {bestGlm5TurboRender.glm5TurboQuota}
                        </div>
                    </div>
                )}

                {(!bestGlm52Render && !bestGlm5TurboRender) && (
                    <div className="text-center py-4 text-gray-400 text-sm">
                        {t('accounts.no_data')}
                    </div>
                )}
            </div>

            {(bestGlm52Render || bestGlm5TurboRender) && onSwitch && (
                <div className="mt-auto pt-3">
                    <button
                        className="w-full px-3 py-1.5 bg-blue-500 text-white text-xs font-medium rounded-lg hover:bg-blue-600 transition-colors"
                        onClick={() => {
                            let targetId = bestGlm52Render?.id;
                            if (bestGlm5TurboRender && (!bestGlm52Render || bestGlm5TurboRender.glm5TurboQuota > bestGlm52Render.glm52Quota)) {
                                targetId = bestGlm5TurboRender.id;
                            }

                            if (onSwitch && targetId) {
                                onSwitch(targetId);
                            }
                        }}
                    >
                        {t('dashboard.switch_best')}
                    </button>
                </div>
            )}
        </div>
    );

}

export default BestAccounts;
