import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Plus, Loader2, CheckCircle2, XCircle, Info, ExternalLink, Key } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { listen } from '@tauri-apps/api/event';
import { request as invoke } from '../../utils/request';

interface AddAccountDialogProps {
    onAdd: (email: string, refreshToken: string) => Promise<void>; // Retained for compatibility
    showText?: boolean;
}

type Status = 'idle' | 'loading' | 'success' | 'error';
type Tab = 'auto' | 'manual';

function AddAccountDialog({ showText = true }: AddAccountDialogProps) {
    const { t } = useTranslation();
    const [isOpen, setIsOpen] = useState(false);
    
    // Tabs
    const [activeTab, setActiveTab] = useState<Tab>('auto');

    // Form inputs
    const [label, setLabel] = useState('');
    const [manualToken, setManualToken] = useState('');

    // UI Status
    const [status, setStatus] = useState<Status>('idle');
    const [message, setMessage] = useState('');

    // Reset state when dialog opens
    useEffect(() => {
        if (isOpen) {
            resetState();
        }
    }, [isOpen]);

    // Listen for events from Tauri backend Webview (for Auto Login)
    useEffect(() => {
        let unlistenSuccess: (() => void) | undefined;
        let unlistenFailure: (() => void) | undefined;

        const setupListeners = async () => {
            unlistenSuccess = await listen<string>('zai-login-success', (event) => {
                setStatus('success');
                setMessage(`${t('common.success', 'Login successful!')} ${t('accounts.add.added', 'Added account')}: ${event.payload}`);
                setTimeout(() => {
                    setIsOpen(false);
                    resetState();
                }, 2000);
            });

            unlistenFailure = await listen<string>('zai-login-failure', (event) => {
                setStatus('error');
                setMessage(event.payload);
            });
        };

        if (isOpen && activeTab === 'auto') {
            setupListeners();
        }

        return () => {
            if (unlistenSuccess) unlistenSuccess();
            if (unlistenFailure) unlistenFailure();
        };
    }, [isOpen, activeTab, t]);

    const resetState = () => {
        setStatus('idle');
        setMessage('');
        setLabel('');
        setManualToken('');
        setActiveTab('auto');
    };

    const handleStartAutoLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        
        setStatus('loading');
        setMessage(t('accounts.add.auto_waiting', 'Please log in inside the new Z.ai window...'));

        try {
            await invoke('start_zai_login', { label: label.trim() || null });
        } catch (error) {
            setStatus('error');
            setMessage(String(error));
        }
    };

    const handleManualSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!manualToken.trim()) {
            setStatus('error');
            setMessage(t('accounts.add.token_required', 'Token or API key is required'));
            return;
        }

        setStatus('loading');
        setMessage(t('accounts.add.saving', 'Validating and saving account...'));

        try {
            const account = await invoke('add_account', { 
                email: label.trim(), 
                refresh_token: manualToken.trim() 
            }) as any;
            setStatus('success');
            setMessage(`${t('common.success', 'Success!')} ${t('accounts.add.added', 'Added account')}: ${account.email}`);
            setTimeout(() => {
                setIsOpen(false);
                resetState();
            }, 2000);
        } catch (error) {
            setStatus('error');
            setMessage(String(error));
        }
    };

    const StatusAlert = () => {
        if (status === 'idle') return null;

        const styles = {
            loading: 'alert-info bg-blue-50 dark:bg-blue-900/10 text-blue-600 dark:text-blue-400 border-blue-100 dark:border-blue-800/30',
            success: 'alert-success bg-emerald-50 dark:bg-emerald-900/10 text-emerald-600 dark:text-emerald-400 border-emerald-100 dark:border-emerald-800/30',
            error: 'alert-error bg-rose-50 dark:bg-rose-900/10 text-rose-600 dark:text-rose-400 border-rose-100 dark:border-rose-800/30',
        };

        const icons = {
            loading: <Loader2 className="w-4 h-4 animate-spin text-blue-500" />,
            success: <CheckCircle2 className="w-4 h-4 text-emerald-500" />,
            error: <XCircle className="w-4 h-4 text-rose-500" />,
        };

        return (
            <div className={`alert ${styles[status]} mb-4 text-sm py-2.5 shadow-sm border rounded-xl flex items-center gap-2.5`}>
                {icons[status]}
                <span className="font-medium break-all">{message}</span>
            </div>
        );
    };

    return (
        <>
            <button
                className="px-2.5 lg:px-4 py-2 bg-white dark:bg-base-100 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-base-200 transition-colors flex items-center gap-2 shadow-sm border border-gray-200/50 dark:border-base-300 relative z-[100]"
                onClick={() => setIsOpen(true)}
                title={!showText ? t('accounts.add_account') : undefined}
            >
                <Plus className="w-4 h-4" />
                {showText && <span className="hidden lg:inline">{t('accounts.add_account')}</span>}
            </button>

            {isOpen && createPortal(
                <div
                    className="fixed inset-0 z-[99999] flex items-center justify-center bg-black/50 backdrop-blur-sm"
                    style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }}
                >
                    {/* Draggable Top Region */}
                    <div data-tauri-drag-region className="fixed top-0 left-0 right-0 h-8 z-[1]" />

                    {/* Click outside to close */}
                    <div className="absolute inset-0 z-[0]" onClick={() => status !== 'loading' && setIsOpen(false)} />

                    <div className="bg-white dark:bg-base-100 text-gray-900 dark:text-base-content rounded-2xl shadow-2xl w-full max-w-md p-6 relative z-[10] m-4 max-h-[90vh] overflow-y-auto border border-gray-200/30 dark:border-base-300/30">
                        <h3 className="font-bold text-lg mb-4">{t('accounts.add.title', 'Add Z.ai Account')}</h3>

                        {/* Tabs Selector */}
                        <div className="tabs tabs-boxed mb-4 bg-gray-50 dark:bg-base-200 p-1 rounded-xl flex border border-gray-200/20 dark:border-base-300/20">
                            <button
                                type="button"
                                className={`flex-1 text-xs py-2 rounded-lg font-medium transition-all ${activeTab === 'auto' ? 'bg-white dark:bg-base-100 shadow-sm text-blue-500 font-semibold' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}`}
                                onClick={() => status !== 'loading' && setActiveTab('auto')}
                                disabled={status === 'loading'}
                            >
                                {t('accounts.add.tab_auto', 'Auto Login')}
                            </button>
                            <button
                                type="button"
                                className={`flex-1 text-xs py-2 rounded-lg font-medium transition-all ${activeTab === 'manual' ? 'bg-white dark:bg-base-100 shadow-sm text-blue-500 font-semibold' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700'}`}
                                onClick={() => status !== 'loading' && setActiveTab('manual')}
                                disabled={status === 'loading'}
                            >
                                {t('accounts.add.tab_manual', 'Manual Entry')}
                            </button>
                        </div>

                        <StatusAlert />

                        {/* Tab 1: Auto Login */}
                        {activeTab === 'auto' && (
                            <form onSubmit={handleStartAutoLogin} className="space-y-4">
                                <div className="p-4 bg-gray-50 dark:bg-base-200 rounded-xl border border-gray-150 dark:border-base-300 text-xs text-gray-500 dark:text-gray-400 space-y-2">
                                    <p className="font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                                        <Info className="w-4 h-4 text-blue-500" />
                                        {t('accounts.add.auto_how_works', 'How it works')}
                                    </p>
                                    <p>
                                        {t('accounts.add.auto_hint', 'Clicking Confirm opens a secure, resizable window pointing to Z.ai. After you log in manually, Z Manager will securely capture your session token automatically and configure the account.')}
                                    </p>
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">
                                        {t('accounts.edit_label', 'Custom Label')} ({t('accounts.add.token.optional', 'Optional')})
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full text-sm py-2.5 px-3 bg-white dark:bg-base-200 border border-gray-200 dark:border-base-300 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all placeholder:text-gray-300 dark:placeholder:text-gray-600 text-gray-800 dark:text-gray-100"
                                        placeholder="e.g. Personal, Work..."
                                        value={label}
                                        onChange={(e) => setLabel(e.target.value)}
                                        disabled={status === 'loading'}
                                    />
                                </div>

                                <div className="flex gap-3 w-full pt-4">
                                    <button
                                        type="button"
                                        className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-base-200 text-gray-700 dark:text-gray-300 font-medium rounded-xl hover:bg-gray-200 dark:hover:bg-base-300 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-200 dark:focus:ring-base-300 text-sm"
                                        onClick={() => setIsOpen(false)}
                                        disabled={status === 'loading'}
                                    >
                                        {t('accounts.add.btn_cancel', 'Cancel')}
                                    </button>
                                    <button
                                        type="submit"
                                        className="flex-1 px-4 py-2.5 text-white font-medium rounded-xl shadow-md transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 bg-blue-500 hover:bg-blue-600 focus:ring-blue-500 shadow-blue-100 dark:shadow-blue-900/30 flex justify-center items-center gap-2 text-sm"
                                        disabled={status === 'loading'}
                                    >
                                        {status === 'loading' ? (
                                            <>
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                <span>{t('accounts.add.waiting', 'Waiting...')}</span>
                                            </>
                                        ) : (
                                            <>
                                                <ExternalLink className="w-4 h-4" />
                                                <span>{t('accounts.add.btn_confirm', 'Confirm')}</span>
                                            </>
                                        )}
                                    </button>
                                </div>
                            </form>
                        )}

                        {/* Tab 2: Manual Entry */}
                        {activeTab === 'manual' && (
                            <form onSubmit={handleManualSubmit} className="space-y-4">
                                <div className="p-4 bg-gray-50 dark:bg-base-200 rounded-xl border border-gray-150 dark:border-base-300 text-xs text-gray-500 dark:text-gray-400 space-y-3">
                                    <p className="font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                                        <Key className="w-4 h-4 text-blue-500" />
                                        {t('accounts.add.manual_how_works', 'Manual Process')}
                                    </p>
                                    <p>
                                        {t('accounts.add.manual_hint', 'Log in to Z.ai using your default web browser, copy your session token (JWT) or generate an API Key, and paste it below.')}
                                    </p>
                                    <div className="pt-1">
                                        <a
                                            href="https://chat.z.ai/api/oauth/authorize?redirect_uri=zcode%3A%2F%2Fzai-auth%2Fcallback&response_type=code&client_id=client_P8X5CMWmlaRO9gyO-KSqtg&state=1dc859b0fcc55bf4953df6004656992c634ef2d69fcb7ec8a2c746616420d5c9"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-base-100 hover:bg-gray-100 dark:hover:bg-base-300 text-xs font-semibold text-blue-500 rounded-lg border border-gray-200/80 dark:border-base-300 transition-colors shadow-sm"
                                        >
                                            <ExternalLink className="w-3.5 h-3.5" />
                                            <span>{t('accounts.add.open_browser', 'Open Z.ai in Browser')}</span>
                                        </a>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">
                                        {t('accounts.edit_label', 'Custom Label')} ({t('accounts.add.token.optional', 'Optional')})
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full text-sm py-2.5 px-3 bg-white dark:bg-base-200 border border-gray-200 dark:border-base-300 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all placeholder:text-gray-300 dark:placeholder:text-gray-600 text-gray-800 dark:text-gray-100"
                                        placeholder="e.g. Secondary Account..."
                                        value={label}
                                        onChange={(e) => setLabel(e.target.value)}
                                        disabled={status === 'loading'}
                                    />
                                </div>

                                <div>
                                    <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1.5 uppercase tracking-wider">
                                        {t('accounts.add.manual_token_label', 'Session Token or API Key')}
                                    </label>
                                    <textarea
                                        className="w-full text-sm py-2.5 px-3 bg-white dark:bg-base-200 border border-gray-200 dark:border-base-300 rounded-xl focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all placeholder:text-gray-300 dark:placeholder:text-gray-600 text-gray-800 dark:text-gray-100 font-mono h-24 resize-none"
                                        placeholder="eyJhbGciOi..."
                                        value={manualToken}
                                        onChange={(e) => setManualToken(e.target.value)}
                                        disabled={status === 'loading'}
                                        required
                                    />
                                </div>

                                <div className="flex gap-3 w-full pt-4">
                                    <button
                                        type="button"
                                        className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-base-200 text-gray-700 dark:text-gray-300 font-medium rounded-xl hover:bg-gray-200 dark:hover:bg-base-300 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-200 dark:focus:ring-base-300 text-sm"
                                        onClick={() => setIsOpen(false)}
                                        disabled={status === 'loading'}
                                    >
                                        {t('accounts.add.btn_cancel', 'Cancel')}
                                    </button>
                                    <button
                                        type="submit"
                                        className="flex-1 px-4 py-2.5 text-white font-medium rounded-xl shadow-md transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 bg-blue-500 hover:bg-blue-600 focus:ring-blue-500 shadow-blue-100 dark:shadow-blue-900/30 flex justify-center items-center gap-2 text-sm font-semibold"
                                        disabled={status === 'loading'}
                                    >
                                        {status === 'loading' ? (
                                            <>
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                <span>{t('accounts.add.saving_btn', 'Saving...')}</span>
                                            </>
                                        ) : (
                                            <span>{t('accounts.add.btn_save', 'Save')}</span>
                                        )}
                                    </button>
                                </div>
                            </form>
                        )}
                    </div>
                </div>,
                document.body
            )}
        </>
    );
}

export default AddAccountDialog;
