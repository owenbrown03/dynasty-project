import { useEffect, useState } from 'react';

import { LoadingState } from '@/components/feedback/LoadingState';
import { useSleeperConnection } from '@/hooks/sleeper/useConnection';
import {
  useCreateReminder,
  useReminders,
  useSaveReminder,
} from '@/hooks/sleeper/useUsers';
import type {
  ReminderItem,
} from '@/types';
import { notify } from '@/utils/notify';

import './RemindersPage.css';


function ReminderCard({
  reminder,
  onSave,
  saving,
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
  saving: boolean;
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
      </div>
    </article>
  );
}


export function RemindersPage() {
  const connection = useSleeperConnection();
  const reminders = useReminders(
    connection.linked,
  );
  const createReminderMutation = useCreateReminder();
  const saveReminderMutation = useSaveReminder();
  const [newTitle, setNewTitle] = useState('');
  const [newNote, setNewNote] = useState('');

  const handleCreate = async () => {
    if (!newTitle.trim()) {
      notify.error('Reminder title is required.');
      return;
    }

    try {
      await createReminderMutation.mutateAsync({
        league_id: null,
        title: newTitle,
        note: newNote,
        due_week: null,
        due_season: null,
        delivery_channel: 'in_app',
      });
      setNewTitle('');
      setNewNote('');
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

  return (
    <main className="reminders-page">
      <section className="reminders-page-header">
        <div>
          <p className="page-eyebrow">Reminders</p>
          <h1 className="reminders-page-title">
            Personal reminders
          </h1>
          <p className="reminders-page-description">
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
                        saving={saveReminderMutation.isPending}
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
