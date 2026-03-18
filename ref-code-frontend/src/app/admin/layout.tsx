'use client';

import { useState, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Sidebar, Menu, MenuItem, SubMenu } from 'react-pro-sidebar';
import { 
  Users, 
  UserCog, 
  Shield, 
  Database, 
  BarChart3, 
  FileText, 
  Lock, 
  Bot,
  UserCheck,
  Layers,
  ClipboardList,
  Activity,
  FileSearch,
  ArrowLeft,
  Link2
} from 'lucide-react';

// Brand green color
const BRAND_GREEN = 'rgb(0,84,64)';
const ICON_SIZE = 20;

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [usersAccessMenuOpen, setUsersAccessMenuOpen] = useState(false);
  const [agentsCorporaMenuOpen, setAgentsCorporaMenuOpen] = useState(false);
  const [monitoringMenuOpen, setMonitoringMenuOpen] = useState(false);
  
  const isActive = (path: string) => {
    if (path === '/admin') {
      return pathname === '/admin';
    }
    return pathname?.startsWith(path);
  };
  
  useEffect(() => {
    // Auto-open Users & Access submenu
    if (pathname?.startsWith('/admin/chatbot-users') ||
        pathname?.startsWith('/admin/chatbot-groups') ||
        pathname?.startsWith('/admin/google-groups') ||
        pathname?.startsWith('/admin/chatbot-agents') ||
        pathname?.startsWith('/admin/chatbot-corpora') ||
        pathname?.startsWith('/admin/agent-assignments')) {
      setUsersAccessMenuOpen(true);
    }
    // Auto-open Agents & Corpora submenu
    if (pathname?.startsWith('/admin/agents') ||
        pathname?.startsWith('/admin/corpora')) {
      setAgentsCorporaMenuOpen(true);
    }
    // Auto-open Monitoring submenu
    if (pathname?.startsWith('/admin/sessions') ||
        pathname?.startsWith('/admin/audit')) {
      setMonitoringMenuOpen(true);
    }
  }, [pathname]);

  const handleMenuClick = (path: string) => {
    router.push(path);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        {/* Sidebar */}
        <Sidebar
          collapsed={collapsed}
          width="280px"
          collapsedWidth="80px"
          backgroundColor="#ffffff"
          rootStyles={{
            borderRight: '1px solid #e5e7eb',
            minHeight: '100vh',
          }}
        >
          <div className="p-6 border-b border-gray-200">
            <h1 className="text-xl font-bold text-gray-900">
              {collapsed ? 'AP' : 'Admin Panel'}
            </h1>
            {!collapsed && (
              <p className="text-sm text-gray-500 mt-1">System Management</p>
            )}
          </div>

          <Menu
            menuItemStyles={{
              button: ({ level, active }) => {
                if (level === 0) {
                  return {
                    backgroundColor: 'transparent',
                    color: '#374151',
                    fontWeight: active ? '700' : '400',
                    padding: '12px 16px',
                    marginBottom: '4px',
                    borderRadius: '8px',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      backgroundColor: '#f3f4f6',
                      color: '#111827',
                    },
                  };
                }
                if (level === 1) {
                  return {
                    backgroundColor: 'transparent',
                    color: '#6b7280',
                    fontWeight: active ? '700' : '400',
                    padding: '10px 16px 10px 48px',
                    marginBottom: '2px',
                    borderRadius: '6px',
                    fontSize: '14px',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      backgroundColor: '#f9fafb',
                      color: '#374151',
                    },
                  };
                }
              },
              subMenuContent: {
                backgroundColor: '#fafafa',
                borderRadius: '8px',
                margin: '4px 8px',
                padding: '4px 0',
              },
            }}
          >
            {/* Active Session Board - Top Level */}
            <MenuItem
              icon={<BarChart3 size={ICON_SIZE} color={BRAND_GREEN} />}
              active={pathname === '/admin'}
              onClick={() => handleMenuClick('/admin')}
            >
              Active Session Board
            </MenuItem>

            {/* Users & Access SubMenu */}
            <SubMenu
              icon={<Users size={ICON_SIZE} color={BRAND_GREEN} />}
              label="Users & Access"
              open={usersAccessMenuOpen}
              onOpenChange={(open) => setUsersAccessMenuOpen(open)}
              rootStyles={{
                '& > .ps-menu-button': {
                  backgroundColor: 'transparent',
                  color: '#374151',
                  fontWeight: usersAccessMenuOpen ? '700' : '400',
                },
              }}
            >
              <MenuItem
                icon={<Users size={ICON_SIZE} color={BRAND_GREEN} />}
                active={isActive('/admin/chatbot-users')}
                onClick={() => handleMenuClick('/admin/chatbot-users')}
              >
                Users
              </MenuItem>
              <MenuItem
                icon={<UserCog size={ICON_SIZE} color={BRAND_GREEN} />}
                active={isActive('/admin/chatbot-groups')}
                onClick={() => handleMenuClick('/admin/chatbot-groups')}
              >
                Groups
              </MenuItem>
              <MenuItem
                icon={<Link2 size={ICON_SIZE} color={BRAND_GREEN} />}
                active={isActive('/admin/google-groups')}
                onClick={() => handleMenuClick('/admin/google-groups')}
              >
                Google Groups Bridge
              </MenuItem>
              <MenuItem
                icon={<ClipboardList size={ICON_SIZE} color={BRAND_GREEN} />}
                active={isActive('/admin/access-matrix')}
                onClick={() => handleMenuClick('/admin/access-matrix')}
              >
                Access Matrix
              </MenuItem>
              <MenuItem
                icon={<Shield size={ICON_SIZE} color={BRAND_GREEN} />}
                active={isActive('/admin/chatbot-agents')}
                onClick={() => handleMenuClick('/admin/chatbot-agents')}
              >
                Agent Access
              </MenuItem>
              <MenuItem
                icon={<Database size={ICON_SIZE} color={BRAND_GREEN} />}
                active={isActive('/admin/chatbot-corpora')}
                onClick={() => handleMenuClick('/admin/chatbot-corpora')}
              >
                Corpora Access
              </MenuItem>
              <MenuItem
                icon={<UserCheck size={ICON_SIZE} color={BRAND_GREEN} />}
                active={isActive('/admin/agent-assignments')}
                onClick={() => handleMenuClick('/admin/agent-assignments')}
              >
                User Agent Assignments
              </MenuItem>
            </SubMenu>

            {/* Agents & Corpora SubMenu */}
            <SubMenu
              icon={<Bot size={ICON_SIZE} color={BRAND_GREEN} />}
              label="Agents & Corpora"
              open={agentsCorporaMenuOpen}
              onOpenChange={(open) => setAgentsCorporaMenuOpen(open)}
              rootStyles={{
                '& > .ps-menu-button': {
                  backgroundColor: 'transparent',
                  color: '#374151',
                  fontWeight: agentsCorporaMenuOpen ? '700' : '400',
                },
              }}
            >
              <MenuItem
                icon={<Bot size={ICON_SIZE} color={BRAND_GREEN} />}
                active={isActive('/admin/agents')}
                onClick={() => handleMenuClick('/admin/agents')}
              >
                Agents
              </MenuItem>
              <MenuItem
                icon={<Layers size={ICON_SIZE} color={BRAND_GREEN} />}
                active={pathname === '/admin/corpora'}
                onClick={() => handleMenuClick('/admin/corpora')}
              >
                Corpora
              </MenuItem>
              <MenuItem
                icon={<Lock size={ICON_SIZE} color={BRAND_GREEN} />}
                active={isActive('/admin/corpora/access')}
                onClick={() => handleMenuClick('/admin/corpora/access')}
              >
                Access Matrix
              </MenuItem>
            </SubMenu>

            {/* Monitoring SubMenu */}
            <SubMenu
              icon={<Activity size={ICON_SIZE} color={BRAND_GREEN} />}
              label="Monitoring"
              open={monitoringMenuOpen}
              onOpenChange={(open) => setMonitoringMenuOpen(open)}
              rootStyles={{
                '& > .ps-menu-button': {
                  backgroundColor: 'transparent',
                  color: '#374151',
                  fontWeight: monitoringMenuOpen ? '700' : '400',
                },
              }}
            >
              <MenuItem
                icon={<Activity size={ICON_SIZE} color={BRAND_GREEN} />}
                active={isActive('/admin/sessions')}
                onClick={() => handleMenuClick('/admin/sessions')}
              >
                Sessions
              </MenuItem>
              <MenuItem
                icon={<FileText size={ICON_SIZE} color={BRAND_GREEN} />}
                active={isActive('/admin/corpora/audit')}
                onClick={() => handleMenuClick('/admin/corpora/audit')}
              >
                Corpus Audit Log
              </MenuItem>
              <MenuItem
                icon={<ClipboardList size={ICON_SIZE} color={BRAND_GREEN} />}
                active={isActive('/admin/audit')}
                onClick={() => handleMenuClick('/admin/audit')}
              >
                System Audit Log
              </MenuItem>
            </SubMenu>
          </Menu>

          {/* Navigation Links */}
          <div className="border-t border-gray-200 mt-4 pt-4 px-4">
            <button
              onClick={() => handleMenuClick('/open-document')}
              className="w-full flex items-center gap-3 px-4 py-3 text-left text-gray-700 hover:bg-gray-50 rounded-lg transition-colors mb-2"
            >
              <FileSearch size={ICON_SIZE} color={BRAND_GREEN} />
              <span className="text-base font-normal">Open Document</span>
            </button>
            <button
              onClick={() => handleMenuClick('/')}
              className="w-full flex items-center gap-3 px-4 py-3 text-left text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
            >
              <ArrowLeft size={ICON_SIZE} color={BRAND_GREEN} />
              <span className="text-base font-normal">Back to App</span>
            </button>
          </div>

          {/* Toggle Button */}
          <div className="absolute bottom-4 right-4">
            <button
              onClick={() => setCollapsed(!collapsed)}
              className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
              title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
            >
              <span className="text-lg">{collapsed ? '→' : '←'}</span>
            </button>
          </div>
        </Sidebar>

        {/* Main Content */}
        <div className="flex-1 overflow-auto">
          {children}
        </div>
      </div>
    </div>
  );
}
