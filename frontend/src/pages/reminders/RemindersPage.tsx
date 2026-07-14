import { useEffect, useState } from 'react';

import { LoadingState } from '@/components/feedback/LoadingState';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import { useLeagueOverview } from '@/hooks/sleeper/useLeagues';
import {
  useCreateReminder,
  useDeleteReminder,
  useReminders,
  useSaveReminder,
  useTestSendReminder,
} from '@/hooks/sleeper/useUsers';
import type {
  ReminderItem,
} from '@/types';
import { notify } from '@/utils/notify';

import './RemindersPage.css';


function ReminderCard({
  reminder,
  onSave,
  onDelete,
  onTestSend,
  saving,
  deleting,
  testingSend,
}: {
  reminder: ReminderItem;
  onSave: (
    reminder: ReminderItem,
    updates: {
      title: string;
      note: string;
      dueWeek: number | null;
      dueSeason: string | null;
      deliveryChannel: string;
      completed: boolean;
    },
  ) => Promise<void>;
  onDelete: (
    reminder: ReminderItem,
  ) => Promise<void>;
  onTestSend: (
    reminder: ReminderItem,
  ) => Promise<void>;
  saving: boolean;
  deleting: boolean;
  testingSend: boolean;
}) {
  const [title, setTitle] = useState(reminder.title);
  const [note, setNote] = useState(reminder.note);
  const [dueWeek, setDueWeek] = useState(
    reminder.due_week?.toString() ?? '',
  );
  const [dueSeason, setDueSeason] = useState(
    reminder.due_season ?? '',
  );
  const [deliveryChannel, setDeliveryChannel] = useState(
    reminder.delivery_channel,
  );
  const [completed, setCompleted] = useState(
    reminder.completed,
  );

  useEffect(() => {
    setTitle(reminder.title);
    setNote(reminder.note);
    setDueWeek(
      reminder.due_week?.toString() ?? '',
    );
    setDueSeason(
      reminder.due_season ?? '',
    );
    setDeliveryChannel(
      reminder.delivery_channel,
    );
    setCompleted(
      reminder.completed,
    );
  }, [reminder]);

  return (
    <article className="reminder-card">
      <div className="reminder-card-header">
        <div>
          <h2>{reminder.title}</h2>
          <p>
            {
              reminder.league_id
                ? `League ${reminder.league_id}`
                : 'General reminder'
            }
          </p>
        </div>

        <label className="reminder-checkbox">
          <input
            type="checkbox"
            checked={completed}
            onChange={(event) => {
              setCompleted(event.target.checked);
            }}
          />
          <span>Done</span>
        </label>
      </div>

      <div className="reminder-form-grid">
        <label>
          <span>Title</span>
          <input
            value={title}
            onChange={(event) => {
              setTitle(event.target.value);
            }}
          />
        </label>

        <label>
          <span>Due season</span>
          <input
            value={dueSeason}
            onChange={(event) => {
              setDueSeason(event.target.value);
            }}
            placeholder="2026"
          />
        </label>

        <label>
          <span>Due week</span>
          <input
            type="number"
            value={dueWeek}
            onChange={(event) => {
              setDueWeek(event.target.value);
            }}
            placeholder="3"
          />
        </label>

        <label>
          <span>Channel</span>
          <select
            value={deliveryChannel}
            onChange={(event) => {
              setDeliveryChannel(event.target.value);
            }}
          >
            <option value="in_app">In app</option>
            <option value="email">Email</option>
          </select>
        </label>
      </div>

      <label className="reminder-note-field">
        <span>Note</span>
        <textarea
          value={note}
          onChange={(event) => {
            setNote(event.target.value);
          }}
        />
      </label>

      <div className="reminder-card-actions">
        {
          deliveryChannel === 'email'
            ? (
              <button
                type="button"
                className="button-secondary"
                disabled={testingSend}
                onClick={() => {
                  void onTestSend(reminder);
                }}
              >
                {
                  testingSend
                    ? 'Testing...'
                    : 'Test email'
                }
              </button>
            )
            : null
        }

        <button
          type="button"
          className="button-secondary"
          disabled={saving}
          onClick={() => {
            void onSave(
              reminder,
              {
                title,
                note,
                dueWeek: dueWeek.trim()
                  ? Number(dueWeek)
                  : null,
                dueSeason: dueSeason.trim() || null,
                deliveryChannel,
                completed,
              },
            );
          }}
        >
          {saving ? 'Saving...' : 'Save'}
        </button>

        <button
          type="button"
          className="button-secondary"
          disabled={deleting}
          onClick={() => {
            void onDelete(reminder);
          }}
        >
          {
            deleting
              ? 'Deleting...'
              : 'Delete'
          }
        </button>
      </div>
    </article>
  );
}


export function RemindersPage() {
  const connection = useSleeperConnection();
  const reminders = useReminders(
    connection.linked,
  );
  const leagueOverview = useLeagueOverview();
  const createReminderMutation = useCreateReminder();
  const saveReminderMutation = useSaveReminder();
  const deleteReminderMutation = useDeleteReminder();
  const testSendReminderMutation = useTestSendReminder();
  const [newTitle, setNewTitle] = useState('');
  const [newNote, setNewNote] = useState('');
  const [newLeagueId, setNewLeagueId] = useState('');
  const [newDueSeason, setNewDueSeason] = useState('');
  const [newDueWeek, setNewDueWeek] = useState('');
  const [newDeliveryChannel, setNewDeliveryChannel] = useState('in_app');

  const handleCreate = async () => {
    if (!newTitle.trim()) {
      notify.error('Reminder title is required.');
      return;
    }

    try {
      await createReminderMutation.mutateAsync({
        league_id: newLeagueId || null,
        title: newTitle,
        note: newNote,
        due_week: newDueWeek.trim()
          ? Number(newDueWeek)
          : null,
        due_season: newDueSeason.trim() || null,
        delivery_channel: newDeliveryChannel,
      });
      setNewTitle('');
      setNewNote('');
      setNewLeagueId('');
      setNewDueSeason('');
      setNewDueWeek('');
      setNewDeliveryChannel('in_app');
      notify.success('Reminder created.');
    } catch {
      notify.error('Unable to create reminder.');
    }
  };

  const handleSave = async (
    reminder: ReminderItem,
    updates: {
      title: string;
      note: string;
      dueWeek: number | null;
      dueSeason: string | null;
      deliveryChannel: string;
      completed: boolean;
    },
  ) => {
    try {
      await saveReminderMutation.mutateAsync({
        id: reminder.id,
        league_id: reminder.league_id,
        title: updates.title,
        note: updates.note,
        due_week: updates.dueWeek,
        due_season: updates.dueSeason,
        delivery_channel: updates.deliveryChannel,
        completed: updates.completed,
      });
      notify.success('Reminder saved.');
    } catch {
      notify.error('Unable to save reminder.');
    }
  };

  const handleDelete = async (
    reminder: ReminderItem,
  ) => {
    try {
      await deleteReminderMutation.mutateAsync({
        id: reminder.id,
      });
      notify.success('Reminder deleted.');
    } catch {
      notify.error('Unable to delete reminder.');
    }
  };

  const handleTestSend = async (
    reminder: ReminderItem,
  ) => {
    try {
      const response = await testSendReminderMutation.mutateAsync({
        id: reminder.id,
      });
      notify.success(
        response.delivery === 'smtp'
          ? `Reminder email sent to ${response.recipient}.`
          : `SMTP is not configured in this environment, so no email was delivered to ${response.recipient}.`,
      );
    } catch {
      notify.error('Unable to test reminder email.');
    }
  };

  return (
    <main className="reminders-page">
      <section className="page-header">
        <div>
          <p className="page-eyebrow">Reminders</p>
          <h1 className="page-title">
            Personal reminders
          </h1>
          <p className="page-description">
            Track in-app reminders now, with optional email delivery when SMTP
            is configured.
          </p>
        </div>
      </section>

      {
        !connection.linked
          ? (
            <div className="reminders-empty-state">
              Link a Sleeper account and log in to manage reminders.
            </div>
          )
          : null
      }

      {
        connection.linked && reminders.loading
          ? (
            <LoadingState
              label="Loading reminders..."
              className="reminders-empty-state"
            />
          )
          : null
      }

      {
        connection.linked && !reminders.loading && reminders.error
          ? (
            <div className="reminders-empty-state">
              Unable to load reminders.
            </div>
          )
          : null
      }

      {
        connection.linked && reminders.data
          ? (
            <>
              <section className="reminder-create-card">
                <h2>Create reminder</h2>

                <div className="reminder-form-grid">
                  <label>
                    <span>Title</span>
                    <input
                      value={newTitle}
                      onChange={(event) => {
                        setNewTitle(event.target.value);
                      }}
                      placeholder="Buy Josh Downs in Week 3"
                    />
                  </label>

                  <label>
                    <span>League</span>
                    <select
                      value={newLeagueId}
                      onChange={(event) => {
                        setNewLeagueId(event.target.value);
                      }}
                    >
                      <option value="">General reminder</option>
                      {
                        leagueOverview.data.map((league) => (
                          <option
                            key={league.league_id}
                            value={league.league_id}
                          >
                            {league.league_name}
                          </option>
                        ))
                      }
                    </select>
                  </label>

                  <label>
                    <span>Due season</span>
                    <input
                      value={newDueSeason}
                      onChange={(event) => {
                        setNewDueSeason(event.target.value);
                      }}
                      placeholder="2026"
                    />
                  </label>

                  <label>
                    <span>Due week</span>
                    <input
                      type="number"
                      value={newDueWeek}
                      onChange={(event) => {
                        setNewDueWeek(event.target.value);
                      }}
                      placeholder="3"
                    />
                  </label>

                  <label>
                    <span>Channel</span>
                    <select
                      value={newDeliveryChannel}
                      onChange={(event) => {
                        setNewDeliveryChannel(event.target.value);
                      }}
                    >
                      <option value="in_app">In app</option>
                      <option value="email">Email</option>
                    </select>
                  </label>
                </div>

                <label className="reminder-note-field">
                  <span>Note</span>
                  <textarea
                    value={newNote}
                    onChange={(event) => {
                      setNewNote(event.target.value);
                    }}
                    placeholder="Coming back from injury and target share should rise."
                  />
                </label>

                <button
                  type="button"
                  className="button-primary"
                  disabled={createReminderMutation.isPending}
                  onClick={() => {
                    void handleCreate();
                  }}
                >
                  {
                    createReminderMutation.isPending
                      ? 'Creating...'
                      : 'Create reminder'
                  }
                </button>
              </section>

              <section className="reminders-grid">
                {
                  reminders.data.reminders.length
                    ? reminders.data.reminders.map((reminder) => (
                      <ReminderCard
                        key={reminder.id}
                        reminder={reminder}
                        onSave={handleSave}
                        onDelete={handleDelete}
                        onTestSend={handleTestSend}
                        saving={saveReminderMutation.isPending}
                        deleting={deleteReminderMutation.isPending}
                        testingSend={testSendReminderMutation.isPending}
                      />
                    ))
                    : (
                      <div className="reminders-empty-state">
                        No reminders yet. Create one for a trade target,
                        injury return, or lineup checkpoint.
                      </div>
                    )
                }
              </section>
            </>
          )
          : null
      }
    </main>
  );
}
